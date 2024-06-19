#   Input variables:
#       1 = working enviroment
#       0 = name for grid and area layer


# import libraries
import arcpy

#Get current map attributes
aprx = arcpy.mp.ArcGISProject("CURRENT")
active_map = aprx.activeMap
spatial_reference = active_map.spatialReference
arcpy.env.overwriteOutput = True

#Set working enviroment
envi = arcpy.GetParameterAsText(1)
arcpy.env.workspace = envi

#variable for layers name
layer_name = arcpy.GetParameterAsText(0)

#Create layer for the total working area
area = arcpy.management.CreateFeatureclass(envi, 'Area_' + layer_name, "POLYGON", '', "ENABLED", '', spatial_reference.name)

#Create domain for crater layer

current_domains = arcpy.da.ListDomains(envi)
current_domain_names = [domain.name for domain in current_domains]
domain = 'Crater type'
if domain not in current_domain_names:
    arcpy.management.CreateDomain(envi, domain, '', 'TEXT', 'CODED')
    craterType = {'Standard':'Standard', 'Marked':'Marked'}
    for code in craterType:
        arcpy.management.AddCodedValueToDomain(envi, domain, code, craterType[code])
else:
    pass

#Create Crater Layer
crater = arcpy.management.CreateFeatureclass(envi, 'Crater_' + layer_name, "POLYGON", '', "ENABLED", '', spatial_reference.name)
arcpy.management.AddField(crater, 'Crater_Type', 'TEXT', '', '', '', 'Crater_Type', 'NON_NULLABLE', 'REQUIRED', domain)


active_map.addDataFromPath(area)
active_map.addDataFromPath(crater)