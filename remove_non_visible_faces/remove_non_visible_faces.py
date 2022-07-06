import sys

import numpy as np
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonCore import vtkIdList, vtkIdTypeArray
from vtkmodules.vtkCommonDataModel import vtkSelection, vtkSelectionNode
from vtkmodules.vtkFiltersCore import vtkCleanPolyData, vtkIdFilter
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkSelectVisiblePoints,
)


def remove_non_visible_faces(
    polydata,
    positions=[[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]],
    remove_visible=False,
):
    polydata.BuildLinks()

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    mapper.Update()

    actor = vtkActor()
    actor.SetMapper(mapper)

    renderer = vtkRenderer()
    renderer.AddActor(actor)

    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)
    render_window.OffScreenRenderingOn()

    camera = renderer.GetActiveCamera()
    renderer.ResetCamera()

    pos = np.array(camera.GetPosition())
    fp = np.array(camera.GetFocalPoint())
    v = pos - fp
    mag = np.linalg.norm(v)
    vn = v / mag

    id_filter = vtkIdFilter()
    id_filter.SetInputData(polydata)
    id_filter.PointIdsOn()
    id_filter.Update()

    set_points = None

    for position in positions:
        pos = fp + np.array(position) * mag
        camera.SetPosition(pos.tolist())
        renderer.ResetCamera()
        render_window.Render()

        select_visible_points = vtkSelectVisiblePoints()
        select_visible_points.SetInputData(id_filter.GetOutput())
        select_visible_points.SetRenderer(renderer)
        #  select_visible_points.SelectInvisibleOn()
        select_visible_points.Update()
        output = select_visible_points.GetOutput()
        id_points = numpy_support.vtk_to_numpy(
            output.GetPointData().GetAbstractArray("vtkIdFilter_Ids")
        )
        if set_points is None:
            set_points = set(id_points.tolist())
        else:
            set_points.update(id_points.tolist())
        #  id_list = vtkIdList()
        #  output.GetVerts().GetCell(1000, id_list)

    if remove_visible:
        set_points = set(range(polydata.GetNumberOfPoints())) - set_points
    cells_ids = set()
    for p_id in set_points:
        id_list = vtkIdList()
        polydata.GetPointCells(p_id, id_list)
        for i in range(id_list.GetNumberOfIds()):
            cells_ids.add(id_list.GetId(i))

    try:
        id_list = numpy_support.numpy_to_vtkIdTypeArray(
            np.array(list(cells_ids), dtype=np.int64)
        )
    except ValueError:
        id_list = vtkIdTypeArray()

    selection_node = vtkSelectionNode()
    selection_node.SetFieldType(vtkSelectionNode.CELL)
    selection_node.SetContentType(vtkSelectionNode.INDICES)
    selection_node.SetSelectionList(id_list)

    selection = vtkSelection()
    selection.AddNode(selection_node)

    extract_selection = vtkExtractSelection()
    extract_selection.SetInputData(0, polydata)
    extract_selection.SetInputData(1, selection)
    extract_selection.Update()

    geometry_filter = vtkGeometryFilter()
    geometry_filter.SetInputData(extract_selection.GetOutput())
    geometry_filter.Update()

    clean_polydata = vtkCleanPolyData()
    clean_polydata.SetInputData(geometry_filter.GetOutput())
    clean_polydata.Update()

    return clean_polydata.GetOutput()


def main():
    from vtkmodules.vtkIOGeometry import vtkSTLReader
    from vtkmodules.vtkIOPLY import vtkPLYWriter

    input_file = sys.argv[1]
    ouput_file = sys.argv[2]

    reader = vtkSTLReader()
    reader.SetFileName(input_file)
    reader.Update()

    output_polydata = remove_nonvisible_faces(
        reader.GetOutput(),
        [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]],
    )

    writer = vtkPLYWriter()
    writer.SetInputData(output_polydata)
    writer.SetFileName(ouput_file)
    writer.Write()


if __name__ == "__main__":
    main()
