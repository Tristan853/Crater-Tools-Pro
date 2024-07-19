import arcpy, math
import arcpy.management

input_polygon = arcpy.GetParameterAsText(0)
grid_size = arcpy.GetParameterAsText(1)
grid_check = arcpy.GetParameterAsText(2)
output_location = arcpy.GetParameterAsText(3)
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

grid_columns = (math.ceil((extent.XMax - extent.XMin)/grid_conversion))
grid_rows = (math.ceil((extent.YMax - extent.YMin)/grid_conversion))


if grid_check == 'true':
    A = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    arcpy.management.AddField(grid, 'ID', 'TEXT')
    arcpy.management.AddField(grid, 'Col', 'LONG')
    arcpy.management.AddField(grid, 'Row', 'LONG')

    with arcpy.da.UpdateCursor(grid, ['OID', 'Col']) as cursor:
        for row in cursor:
            R = math.floor(row[0]/grid_columns)
            if row[0] <= grid_columns:
                row[1] = row[0]
            elif row[0] - (R * grid_columns) == 0:
                row[1] = row[0] - (((R - 1) * grid_columns))
            else:
                row[1] = row[0] - (R * grid_columns)                   
            cursor.updateRow(row)

    with arcpy.da.UpdateCursor(grid, ['OID', 'Row']) as cursor:
        for row in cursor:
            R = math.ceil(row[0]/grid_columns)
            RN = R - (grid_rows + 1)
            row[1] = abs(RN)
            cursor.updateRow(row)
    
    with arcpy.da.UpdateCursor(grid, ['Col', 'Row', 'ID']) as cursor:
        for row in cursor:
                N = row[0]
                O = math.floor(row[0]/len(A))
                if N <= len(A):
                    row[2] = A[N - 1] + str(row[1])
                    cursor.updateRow(row)
                if N > len(A):
                    P = (N - (O * len(A)))
                    if P == 0:
                        row[2] = A[O - 2] + A[P - 1] + str(row[1])
                        cursor.updateRow(row)
                    if P <= len(A) and P > 0:                
                        row[2] = A[O - 1] + A[P - 1] + str(row[1])
                        cursor.updateRow(row)
else:
    pass


active_map.addDataFromPath(grid)