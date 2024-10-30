import arcpy, math, datetime, time, os

import arcpy.da
import arcpy.management
workspace = arcpy.env.workspace
arcpy.env.overwriteOutput = True
crater_layer = arcpy.GetParameterAsText(0)
area_layer = arcpy.GetParameterAsText(1)
approach = arcpy.GetParameterAsText(2)
folder = arcpy.GetParameterAsText(3)
fname = os.path.join(folder, arcpy.GetParameterAsText(4))
file_type = arcpy.GetParameterAsText(5)
if file_type == 'SCC':
	stats_file_output = fname + '.scc'
elif file_type == 'DIAM':
	stats_file_output = fname + '.diam'
area_name = crater_layer.split("\\")

desc = arcpy.Describe(crater_layer)
sr = desc.spatialReference
major_axis = sr.semiMajorAxis
minor_axis = sr.semiMinorAxis
sr_name = sr.name

def internal_reproject():
    in_sr=arcpy.Describe(crater_layer).spatialReference
    arcpy.env.outputCoordinateSystem = in_sr
    #convert crater feature vertices to points
    crater_vertices = arcpy.management.FeatureVerticesToPoints(crater_layer, crater_layer + '_vertices', 'START')
    crater_vertices1 = arcpy.management.FeatureVerticesToPoints(crater_layer, crater_layer + '_vertices1', 'MID')
    #create diameter line
    vertices_merge = workspace + r'\vertices_merge'
    crater_diameter = workspace + r'\crater_diameter'
    arcpy.management.Merge([crater_vertices, crater_vertices1], vertices_merge)
    arcpy.management.PointsToLine(vertices_merge, crater_diameter,'ORIG_FID')
    #find center
    crater_center = workspace + r'\crater_center'
    arcpy.management.FeatureVerticesToPoints(crater_diameter, crater_center, 'MID')
    #calculate coordinates
    xy_fields = [['X_coordinate', 'POINT_X'], ['Y_coordinate', 'POINT_Y']]
    center_fields = [['Center_X', 'POINT_X'], ['Center_Y', 'POINT_Y']]
    arcpy.management.CalculateGeometryAttributes(vertices_merge, xy_fields, '', '', in_sr, 'DD')
    arcpy.management.CalculateGeometryAttributes(crater_center, center_fields, '', '', in_sr, 'DD')
    #add center coordinates to dictionary
    OID_dict={}
    with arcpy.da.UpdateCursor(crater_diameter, ['OBJECTID','ORIG_FID']) as cursor:
        for row in cursor:
            OID_dict.update({row[0]:row[1]})
    del cursor
    center_coords = {}
    with arcpy.da.UpdateCursor(crater_center, ['ORIG_FID', 'Center_X', 'Center_Y']) as cursor:
        for row in cursor:
            row[0]=OID_dict[row[0]]
            cursor.updateRow(row)
            center_coords.update({row[0]: [row[1], row[2]]})
    del cursor
    #assign coordinates to vertices
    arcpy.management.AddFields(vertices_merge, [['Center_X', 'DOUBLE'], ['Center_Y', 'DOUBLE']])
    with arcpy.da.UpdateCursor(vertices_merge, ['ORIG_FID', 'Center_X', 'Center_Y']) as cursor:
        for row in cursor:
            row[1]=center_coords[row[0]][0]
            row[2]=center_coords[row[0]][1]
            cursor.updateRow(row)
    del cursor
    true_scale_craters=arcpy.management.CreateFeatureclass(out_path=workspace, out_name='True_Scale_Craters', geometry_type='POLYGON')
    arcpy.management.AddField(true_scale_craters.getOutput(0), 'Area', 'DOUBLE')
    #reproject points to stereographic projection
    craterSR = arcpy.Describe(crater_layer).spatialReference
    Gcs = craterSR.GCS
    Gcs_string = Gcs.exportToString()
    clean_gcs_wkt = Gcs_string.split("];")[0] + "]"
    stereo_scratch = workspace + r'\stereo_scratch'
    stereo_append = workspace + r'\stereo_append'
    arcpy.management.CreateFeatureclass(out_path=workspace, out_name='stereo_append', geometry_type='POLYGON')
    x=1
    with arcpy.da.UpdateCursor(vertices_merge, ['Center_X', 'Center_Y', 'ORIG_FID']) as cursor:
        vertices_layer = "vertices_merge_layer"
        arcpy.management.MakeFeatureLayer(vertices_merge, vertices_layer)
        feature_count = int(arcpy.management.GetCount(vertices_merge)[0])
        for row in cursor:
            arcpy.AddMessage(str(x))
            arcpy.AddMessage(str([row[2]]))
            # while x <= feature_count:
            if x == row[2]:
                arcpy.AddMessage('match')
                central_meridian = row[0]
                latitude_of_origin = row[1]
                projection_params = {
                    "GEOGCS": clean_gcs_wkt,
                    "PROJECTION": "Stereographic",
                    "central_meridian": central_meridian,
                    "scale_factor": 1.0,
                    "false_easting": 0.0,
                    "false_northing": 0.0,
                    "latitude_of_origin": latitude_of_origin
                }

                # Create the WKT string
                wkt_template = (
                'PROJCS["Custom_Stereographic",'
                '{GEOGCS},'
                'PROJECTION["{PROJECTION}"],'
                'PARAMETER["Central_Meridian",{central_meridian}],'
                'PARAMETER["Scale_Factor",{scale_factor}],'
                'PARAMETER["False_Easting",{false_easting}],'
                'PARAMETER["False_Northing",{false_northing}],'
                'PARAMETER["Latitude_Of_Origin",{latitude_of_origin}],'
                'UNIT["Meter",1.0]]'
                )
                wkt = wkt_template.format(
                    GEOGCS=projection_params["GEOGCS"],
                    PROJECTION=projection_params["PROJECTION"],
                    central_meridian=projection_params["central_meridian"],
                    scale_factor=projection_params["scale_factor"],
                    false_easting=projection_params["false_easting"],
                    false_northing=projection_params["false_northing"],
                    latitude_of_origin=projection_params["latitude_of_origin"]
                )
                nsr = arcpy.SpatialReference()
                nsr.loadFromString(wkt)
                arcpy.env.outputCoordinateSystem = nsr
                query = f"ORIG_FID = {x}"
                arcpy.management.SelectLayerByAttribute(vertices_layer, 'NEW_SELECTION', query)
                arcpy.management.MinimumBoundingGeometry(vertices_layer, stereo_scratch, 'CIRCLE', 'ALL')
                arcpy.management.SelectLayerByAttribute(vertices_layer, 'CLEAR_SELECTION')
                arcpy.management.Append(stereo_scratch, stereo_append, 'NO_TEST')
                x+=1
            else:
                arcpy.AddMessage('no match')
                x+=1
    del cursor
    with arcpy.da.SearchCursor(stereo_append, ['OBJECTID']) as cursor:
        for row in cursor:                   
            #project circle into sinusoidal projection
            central_meridian = row[0]
            latitude_of_origin = row[1]
            projection_params = {
            "GEOGCS": clean_gcs_wkt,
            "PROJECTION": "Sinusoidal",
            "central_meridian": central_meridian,  # Central meridian as a float or integer
            "scale_factor": 1,                     # Scale factor as a float
            "false_easting": 0,                    # False easting as a float
            "false_northing": 0,                   # False northing as a float
            "latitude_of_origin": latitude_of_origin  # Latitude of origin as a float or integer
            }

            # Create the WKT string
            sinusoidal_wkt_template = (
            'PROJCS["Custom_Sinusoidal",'
            '{GEOGCS},'
            'PROJECTION["{PROJECTION}"],'
            'PARAMETER["Central_Meridian",{central_meridian}],'
            'PARAMETER["Scale_Factor",{scale_factor}],'
            'PARAMETER["False_Easting",{false_easting}],'
            'PARAMETER["False_Northing",{false_northing}],'
            'PARAMETER["Latitude_Of_Origin",{latitude_of_origin}],'
            'UNIT["Meter",1.0]]'
            )

            sinusoidal_wkt = sinusoidal_wkt_template.format(
            GEOGCS=projection_params["GEOGCS"],
            PROJECTION=projection_params["PROJECTION"],
            central_meridian=projection_params["central_meridian"],
            scale_factor=projection_params["scale_factor"],
            false_easting=projection_params["false_easting"],
            false_northing=projection_params["false_northing"],
            latitude_of_origin=projection_params["latitude_of_origin"]
            )
            ssr=arcpy.SpatialReference()
            ssr.loadFromString(sinusoidal_wkt)
            arcpy.env.outputCoordinateSystem = ssr
            #project undistorted circle
            sinusoidal_projected_circle = workspace + r'\sinusoidal_craters'
            arcpy.management.Project(stereo_append, sinusoidal_projected_circle, ssr)
            arcpy.management.CalculateGeometryAttributes(sinusoidal_projected_circle, [['Area', 'AREA']], '', 'SQUARE_METERS')
            arcpy.management.Append(sinusoidal_projected_circle, true_scale_craters.getOutput(0), 'NO_TEST')            
                    
        
    arcpy.management.AddField(true_scale_craters, 'Diameter', 'DOUBLE')
    with arcpy.da.UpdateCursor(true_scale_craters, ['Area', 'Diameter']) as cursor:
        for row in cursor:
            row[1] = 2 * math.sqrt(row[0]/math.pi)
            cursor.updateRow(row)
    del cursor
    arcpy.management.CalculateGeometryAttributes(true_scale_craters, [['Center_X', 'INSIDE_X'], ['Center_Y', 'INSIDE_Y']], '','','', 'DD')
    # delete_list = [stereo_scratch, sinusoidal_projected_circle, vertices_merge, vertices_layer, crater_vertices, crater_vertices1, crater_center, crater_diameter]
    # for x in delete_list:
    #     arcpy.management.Delete(x)

def area_reprojection():
     area_center = workspace + r'\area_center'
     arcpy.management.FeatureToPoint(area_layer, area_center, 'INSIDE')
     arcpy.management.CalculateGeometryAttributes(area_center, [['Center_X', 'POINT_X'], ['Center_Y', 'POINT_Y']], '', '', '', 'DD')
     #calculate area with sinusoidal projection with area center as central meridian
     craterSR = arcpy.Describe(crater_layer).spatialReference
     Gcs = craterSR.GCS
     Gcs_string = Gcs.exportToString()
     clean_gcs_wkt = Gcs_string.split("];")[0] + "]"
     
     with arcpy.da.SearchCursor(area_center, ['Center_X', 'Center_Y']) as cursor:
          for row in cursor:
            central_meridian = row[0]
            latitude_of_origin = row[1]
            projection_params = {
                "GEOGCS": clean_gcs_wkt,
                "PROJECTION": "Sinusoidal",
                "central_meridian": central_meridian,  # Central meridian as a float or integer
                "scale_factor": 1,                     # Scale factor as a float
                "false_easting": 0,                    # False easting as a float
                "false_northing": 0,                   # False northing as a float
                "latitude_of_origin": latitude_of_origin  # Latitude of origin as a float or integer
                }

            #Create the WKT string
            sinusoidal_wkt_template = (
                'PROJCS["Custom_Sinusoidal",'
                '{GEOGCS},'
                'PROJECTION["{PROJECTION}"],'
                'PARAMETER["Central_Meridian",{central_meridian}],'
                'PARAMETER["Scale_Factor",{scale_factor}],'
                'PARAMETER["False_Easting",{false_easting}],'
                'PARAMETER["False_Northing",{false_northing}],'
                'PARAMETER["Latitude_Of_Origin",{latitude_of_origin}],'
                'UNIT["Meter",1.0]]'
            )
            
            sinusoidal_wkt = sinusoidal_wkt_template.format(
                GEOGCS=projection_params["GEOGCS"],
                PROJECTION=projection_params["PROJECTION"],
                central_meridian=projection_params["central_meridian"],
                scale_factor=projection_params["scale_factor"],
                false_easting=projection_params["false_easting"],
                false_northing=projection_params["false_northing"],
                latitude_of_origin=projection_params["latitude_of_origin"]
                )
            ssr=arcpy.SpatialReference()
            ssr.loadFromString(sinusoidal_wkt)
            arcpy.management.CalculateGeometryAttributes(area_layer, [['Area', 'AREA']], '', 'SQUARE_KILOMETERS', ssr)
     arcpy.management.FeatureVerticesToPoints(area_layer, workspace + r'\area_vertices', 'ALL')
     arcpy.management.CalculateGeometryAttributes(workspace + r'\area_vertices', [['X', 'POINT_X'], ['Y', 'POINT_Y']], '', '', '', 'DD')

def write_crater_stats_file(stats_file):
    now = datetime.datetime.now()
    date = str(now.day) + "." + str(now.month) + "." + str(now.year)
    vertices = workspace + r'\area_vertices'
    true_scale_craters = workspace + r'\true_scale_craters'
    if os.path.exists(stats_file) == False:
        open(stats_file, 'x')
    else:
        pass

    crater_stats_file = open(stats_file, "w")

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
        with arcpy.da.SearchCursor(area_layer, 'Area') as cursor:
            for row in cursor:
                vertex_count = 1
                crater_stats_file.write("#\n"\
                                        "# Area_name " + str(n_area) + " = " + str(area_name) + "\n"\
                                        "# Area_size " + str(n_area) + " = " + str(row[0]) + " <km^2>\n"\
                                        "#\n")		
                with arcpy.da.SearchCursor(vertices, ['X', 'Y', 'ORIG_FID']) as cursor:
                    for row in cursor:
                        if row[2] == n_area:
                            crater_stats_file.write(str(vertex_count) + "\t" + str(1) + "\text\t" + str(row[0]) + "\t" + str(row[1]) + "\n")
                            vertex_count += 1
            n_area += 1
        with arcpy.da.SearchCursor(area_layer, 'Area') as cursor:
                total_area = sum(row[0] for row in cursor)
                crater_stats_file.write("}\n"\
                                        "#\n"\
                                        "Total_area = " + str(total_area) + " <km^2>\n"\
                                        "#\n"\
                                        "# crater_diameters: \n"\
                                        "crater = {diam, fraction, lon, lat\n")

        with arcpy.da.SearchCursor(true_scale_craters, ['Diameter', 'Center_X', 'Center_Y']) as cursor:						
            for row in cursor:
                 crater_stats_file.write(str(row[0]/1000) + "\t" + '1' + "\t" + str(row[1]) + "\t" + str(row[2]) + "\n")
        crater_stats_file.write("}")
        crater_stats_file.close()

    if file_type == "DIAM":
            crater_stats_file.write("# Diam file for Craterstats - " + methodology_name + "\n"\
                                "#\n"\
                                "# Date of measurement export = " + str(date) + "\n"\
                                "#\n")
            
internal_reproject()
area_reprojection()
write_crater_stats_file(stats_file_output)