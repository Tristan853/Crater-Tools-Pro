import arcpy, math, datetime, time, os

arcpy.env.overwriteOutput = True
scratch = arcpy.env.scratchGDB
crater_layer = arcpy.GetParameterAsText(0)
coor_system = arcpy.GetParameterAsText(1)
approach = arcpy.GetParameterAsText(2)
file_type = arcpy.GetParameterAsText(5)
folder = arcpy.GetParameterAsText(3)
fname = os.path.join(folder, arcpy.GetParameterAsText(4))
area_layer = arcpy.GetParameterAsText(6)
if file_type == 'SCC':
	stats_file_output = fname + '.scc'
elif file_type == 'DIAM':
	stats_file_output = fname + '.diam'
an = crater_layer.split("\\")

coor_system_list = {'DD': 'DD', 'DMS': 'DMS_DIR_LAST'}
field_list = [['Centroid_X', 'CENTROID_X'], ['Centroid_Y', 'CENTROID_Y']]
arcpy.management.AddFields(crater_layer, [['Centroid_X', 'TEXT', 'Centroid X'], ['Centroid_Y', 'TEXT', 'Centroid Y'], ['Diameter', 'DOUBLE']])
arcpy.management.CalculateGeometryAttributes(crater_layer, field_list, '', '', '', coor_system_list[coor_system])
Area = arcpy.management.CalculateGeometryAttributes(area_layer, [['A', 'AREA_GEODESIC']], '', 'SQUARE_KILOMETERS')
with arcpy.da.SearchCursor(area_layer, 'A') as cursor:
     for row in cursor:
          Area_Size = row[0]
arcpy.management.CalculateGeometryAttributes(crater_layer, [['Area', 'AREA_GEODESIC']], '', 'SQUARE_KILOMETERS')
with arcpy.da.UpdateCursor(crater_layer, ['Area', 'Diameter']) as cursor:
    for row in cursor:
        row[1] = 2 * (math.sqrt(row[0] / math.pi))
        cursor.updateRow(row)

v_layer = os.path.join(scratch, 'Vertices')
vertices = arcpy.management.FeatureVerticesToPoints(area_layer, v_layer)
arcpy.management.AddFields(vertices, [['X', 'TEXT'], ['Y', 'TEXT']])
arcpy.management.CalculateGeometryAttributes(vertices, [['X', 'POINT_X'],['Y', 'POINT_Y']], '', '', '', coor_system_list[coor_system])

""" Write SCC/DIAM file header """

def write_crater_stats_file():
    now = datetime.datetime.now()
    date = str(now.day) + "." + str(now.month) + "." + str(now.year)
    desc = arcpy.Describe(crater_layer)
    sr = desc.spatialReference
    major_axis = sr.semiMajorAxis
    minor_axis = sr.semiMinorAxis
    sr_name = sr.name

    if sr.type == 'Projected':
         arcpy.AddError('Spatial reference must be a geographic coordinate system.')
    else:
         pass

    if os.path.exists(stats_file_output) == False:
        open(stats_file_output, 'x')
    else:
        pass

    crater_stats_file = open(stats_file_output, "w")

    if approach == "BCC":
        methodology_name = "Buffered crater count"

    if approach == "TRAD":
        methodology_name = "Traditional crater counting approach"

    if approach == "NSC":
        methodology_name = "Non-sparseness correction"

    if approach == "BNSC":
        methodology_name = "Buffered non-sparseness correction"

    if file_type == "SCC":
        n_area = 1
        crater_stats_file.write("# Spatial crater count for Craterstats - " + methodology_name + "\n"\
                                "#\n"\
                                "# Date of measurement = " + str(date) + "\n"\
                                "#\n"\
                                "# Ellipsoid axes: " + str(major_axis) + "\n"\
                                "a-axis radius = " + str(major_axis/1000) + " <km>\n"\
                                "b-axis radius = " + str(minor_axis/1000) + " <km>\n"\
                                "c-axis radius = " + str(minor_axis/1000) + " <km>\n"\
                                "coordinate_system_name = " + str(sr_name) + "\n"\
                                "#\n"\
                                "# area_shapes:\n"\
                                "unit_boundary = {vertex, sub_area, tag, lon, lat\n")
        crater_stats_file.write("#\n"\
								"# Area_name " + str(n_area) + " = " + str(an) + "\n"\
								"# Area_size " + str(n_area) + " = " + str(Area_Size) + " <km^2>\n"\
								"#\n")
        if n_area == 1:
            vertex_count = 1
		
        with arcpy.da.SearchCursor(vertices, ['X', 'Y']) as cursor:
             for row in cursor:
                crater_stats_file.write(str(vertex_count) + "\t" + str(1) + "\text\t" + str(row[0]) + "\t" + str(row[1]) + "\n")
                vertex_count += 1
		
        crater_stats_file.write("}\n"\
								"#\n"\
								"Total_area = " + str(Area_Size) + " <km^2>\n"\
								"#\n"\
								"# crater_diameters: \n"\
								"crater = {diam, fraction, lon, lat\n")

        with arcpy.da.SearchCursor(crater_layer, ['Diameter', 'Centroid_X', 'Centroid_Y']) as cursor:						
            for row in cursor:
                 crater_stats_file.write(str(row[0]) + "\t" + '1' + "\t" + str(row[1]) + "\t" + str(row[2]) + "\n")
        crater_stats_file.write("}")
        crater_stats_file.close()

    if file_type == "DIAM":
            crater_stats_file.write("# Diam file for Craterstats - " + methodology_name + "\n"\
                                "#\n"\
                                "# Date of measurement export = " + str(date) + "\n"\
                                "#\n")
            
write_crater_stats_file()