import arcpy
import arcpy.management

input_polygon = arcpy.GetParameterAsText(0)
grid_size = arcpy.GetParameterAsText(1)
output_location = arcpy.GetParameterAsText(2)
intGrid = int(grid_size)
grid_conversion = (intGrid * 1000)


aprx = arcpy.mp.ArcGISProject("CURRENT")
active_map = aprx.activeMap
arcpy.env.overwriteOutput = True
arcpy.env.workspace = output_location
desc = arcpy.Describe(input_polygon)
arcpy.env.outputCoordinateSystem = desc.spatialReference

layer_name = input_polygon.split('\\')
extent = desc.extent
grid = arcpy.management.CreateFishnet(output_location + r'\Grid_' + layer_name[-1].split('_')[-1], str(extent.XMin) + " " + str(extent.YMin), str(extent.XMin) + " " + str(extent.YMax), grid_conversion, grid_conversion, number_rows='0', number_columns='0',corner_coord=str(extent.XMax) + " " + str(extent.YMax) , labels="NO_LABELS", template='#', geometry_type='POLYGON')

active_map.addDataFromPath(grid)