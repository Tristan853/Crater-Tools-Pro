import arcpy
import arcpy.management

input_polygon = arcpy.GetParameterAsText(0)
grid_size = arcpy.GetParameterAsText(1)
output_location = arcpy.GetParameterAsText(2)



aprx = arcpy.mp.ArcGISProject("CURRENT")
active_map = aprx.activeMap
arcpy.env.overwriteOutput = True
arcpy.env.workspace = output_location

layer_name = input_polygon.split('\\')
origin = arcpy.management.CalculateGeometryAttributes(input_polygon, [['Center_X', 'CENTROID_X'],['Center_Y', 'CENTROID_Y']], '', '', '', 'DD')
field = ['Center_X', 'Center_Y']
with arcpy.da.SearchCursor(origin, field) as cursor:
    for row in cursor:
        xy = row
coord = str(xy[0]) + ' ' + str(xy[1])
newYcoord = xy[1] + 0.05
ycoord = str(xy[0]) + ' ' + str(newYcoord)
grid = arcpy.management.CreateFishnet(output_location + r'\Grid_' + layer_name[-1].split('_')[-1], coord, ycoord, grid_size, grid_size, '0', '0', '', 'NO_LABELS', 'MINOF', 'POLYGON')

active_map.addDataFromPath(grid)