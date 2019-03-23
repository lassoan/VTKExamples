#!/usr/bin/env python

import vtk


def get_program_parameters():
    import argparse
    description = 'Read a polydata file of a surface and determine if it is a closed surface.'
    epilogue = '''
This example illustrates how to extract the cells that exist inside a closed surface.
It uses vtkSelectEnclosedPoints to mark points that are inside and outside the surface.
vtkMultiThreshold is used to extract the three meshes into three vtkMultiBlockDataSet's.
The cells completely outside are shown in crimson, completely inside are yellow and
 border cells are green.
A translucent copy of the closed surface helps illustrate the selection process.

If two polydata datasets are provided, the example uses the second as the closed surface.
If only one dataset is provided, the closed surface is generated by rotating the
 first dataset by 90 degrees around its Y axis.

   '''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filename1', help='Enter a polydata file e.g cow.g.')
    parser.add_argument('filename2', default=None, nargs='?', help='Enter another polydata file e.g cow.g.')
    args = parser.parse_args()
    return args.filename1, args.filename2


def ReadPolyData(file_name):
    import os
    path, extension = os.path.splitext(file_name)
    extension = extension.lower()
    if extension == ".ply":
        reader = vtk.vtkPLYReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".vtp":
        reader = vtk.vtkXMLpoly_dataReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".obj":
        reader = vtk.vtkOBJReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".stl":
        reader = vtk.vtkSTLReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".vtk":
        reader = vtk.vtkpoly_dataReader()
        reader.SetFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    elif extension == ".g":
        reader = vtk.vtkBYUReader()
        reader.SetGeometryFileName(file_name)
        reader.Update()
        poly_data = reader.GetOutput()
    else:
        # Return a None if the extension is unknown.
        poly_data = None
    return poly_data


def main():
    fn1, fn2 = get_program_parameters()
    polyData1 = ReadPolyData(fn1)
    if fn2:
        polyData2 = ReadPolyData(fn1)
    else:
        # If only one polydata is present, generate a second polydata by
        # rotating the original about its center.
        print('Generating modified polyData1')
        center = polyData1.GetCenter()
        transform = vtk.vtkTransform()
        transform.Translate(center[0], center[1], center[2])
        transform.RotateY(90.0)
        transform.Translate(-center[0], -center[1], -center[2])
        transformPD = vtk.vtkTransformPolyDataFilter()
        transformPD.SetTransform(transform)
        transformPD.SetInputData(polyData1)
        transformPD.Update()
        polyData2 = transformPD.GetOutput()

    # Mark points inside with 1 and outside with a 0
    select = vtk.vtkSelectEnclosedPoints()
    select.SetInputData(polyData1)
    select.SetSurfaceData(polyData2)

    # Extract three meshes, one completely inside, one completely
    # outside and on the border between the inside and outside.

    threshold = vtk.vtkMultiThreshold()
    # Outside points have a 0 value in ALL points of a cell
    outsideId = threshold.AddBandpassIntervalSet(
        0, 0,
        vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "SelectedPoints",
        0, 1)
    # Inside points have a 1 value in ALL points of a cell
    insideId = threshold.AddBandpassIntervalSet(
        1, 1,
        vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "SelectedPoints",
        0, 1)
    # Border points have a 0 or a 1 in at least one point of a cell
    borderId = threshold.AddIntervalSet(
        0, 1,
        vtk.vtkMultiThreshold.OPEN, vtk.vtkMultiThreshold.OPEN,
        vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "SelectedPoints",
        0, 0)

    threshold.SetInputConnection(select.GetOutputPort())

    # Select the intervals to be output
    threshold.OutputSet(outsideId)
    threshold.OutputSet(insideId)
    threshold.OutputSet(borderId)
    threshold.Update()

    # Visualize
    colors = vtk.vtkNamedColors()
    outsideColor = colors.GetColor3d("Crimson")
    insideColor = colors.GetColor3d("Banana")
    borderColor = colors.GetColor3d("Mint")
    surfaceColor = colors.GetColor3d("Peacock")
    backgroundColor = colors.GetColor3d("Silver")

    # Outside
    outsideMapper = vtk.vtkDataSetMapper()
    outsideMapper.SetInputData(threshold.GetOutput().GetBlock(outsideId).GetBlock(0))
    outsideMapper.ScalarVisibilityOff()

    outsideActor = vtk.vtkActor()
    outsideActor.SetMapper(outsideMapper)
    outsideActor.GetProperty().SetDiffuseColor(outsideColor)
    outsideActor.GetProperty().SetSpecular(.6)
    outsideActor.GetProperty().SetSpecularPower(30)

    # Inside
    insideMapper = vtk.vtkDataSetMapper()
    insideMapper.SetInputData(threshold.GetOutput().GetBlock(insideId).GetBlock(0))
    insideMapper.ScalarVisibilityOff()

    insideActor = vtk.vtkActor()
    insideActor.SetMapper(insideMapper)
    insideActor.GetProperty().SetDiffuseColor(insideColor)
    insideActor.GetProperty().SetSpecular(.6)
    insideActor.GetProperty().SetSpecularPower(30)
    insideActor.GetProperty().EdgeVisibilityOn()

    # Border
    borderMapper = vtk.vtkDataSetMapper()
    borderMapper.SetInputData(threshold.GetOutput().GetBlock(borderId).GetBlock(0))
    borderMapper.ScalarVisibilityOff()

    borderActor = vtk.vtkActor()
    borderActor.SetMapper(borderMapper)
    borderActor.GetProperty().SetDiffuseColor(borderColor)
    borderActor.GetProperty().SetSpecular(.6)
    borderActor.GetProperty().SetSpecularPower(30)
    borderActor.GetProperty().EdgeVisibilityOn()

    surfaceMapper = vtk.vtkDataSetMapper()
    surfaceMapper.SetInputData(polyData2)
    surfaceMapper.ScalarVisibilityOff()

    # Surface of object containing cell
    surfaceActor = vtk.vtkActor()
    surfaceActor.SetMapper(surfaceMapper)
    surfaceActor.GetProperty().SetDiffuseColor(surfaceColor)
    surfaceActor.GetProperty().SetOpacity(.1)

    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetSize(640, 480)

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    renderer.SetBackground(backgroundColor)
    renderer.UseHiddenLineRemovalOn()

    renderer.AddActor(surfaceActor)
    renderer.AddActor(outsideActor)
    renderer.AddActor(insideActor)
    renderer.AddActor(borderActor)

    renderWindow.SetWindowName('CellsInsideObject')
    renderWindow.Render()
    renderer.GetActiveCamera().Azimuth(30)
    renderer.GetActiveCamera().Elevation(30)
    renderer.GetActiveCamera().Dolly(1.25)
    renderWindow.Render()

    renderWindowInteractor.Start()


if __name__ == '__main__':
    main()
