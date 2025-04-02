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

#set symbology
area_layer = active_map.listLayers(f"Area_{layer_name}")[0]
if area_layer.isFeatureLayer:
    try:
        # Get the CIM definition of the layer
        cim_layer = area_layer.getDefinition('V3')

        # Ensure the layer has a renderer
        if hasattr(cim_layer, "renderer") and cim_layer.renderer:
            # Access the symbol reference
            cim_symbol_ref = cim_layer.renderer.symbol
            cim_symbol = cim_symbol_ref.symbol  # Get the actual CIMPolygonSymbol

            # Check if the CIM symbol is valid
            if cim_symbol:
                stroke=cim_symbol.symbolLayers[0]
                stroke.color.values = [0, 0, 0, 255]
                stroke.width = 2

                fill=cim_symbol.symbolLayers[1]
                fill.color.values=[255, 255, 255, 0]
                
                # Assign the modified symbol back to the renderer
                area_layer.setDefinition(cim_layer)

        arcpy.AddMessage("Symbology applied successfully.")

    except Exception as e:
        arcpy.AddMessage(f"Failed to apply symbology: {e}")

crater_layer = active_map.listLayers(f"Crater_{layer_name}")[0]
if crater_layer.isFeatureLayer:
    try:
        # Get the CIM definition of the layer
        cim_layer = crater_layer.getDefinition('V3')

        # Ensure the layer has a renderer
        if hasattr(cim_layer, "renderer") and cim_layer.renderer:
            # Access the symbol reference
            cim_symbol_ref = cim_layer.renderer.symbol
            cim_symbol = cim_symbol_ref.symbol  # Get the actual CIMPolygonSymbol

            # Check if the CIM symbol is valid
            if cim_symbol:
                stroke=cim_symbol.symbolLayers[0]
                stroke.color.values = [0, 255, 0, 255]
                stroke.width = 2

                fill=cim_symbol.symbolLayers[1]
                fill.color.values=[255, 255, 255, 0]
                
                # Assign the modified symbol back to the renderer
                crater_layer.setDefinition(cim_layer)

        arcpy.AddMessage("Symbology applied successfully.")

    except Exception as e:
        arcpy.AddMessage(f"Failed to apply symbology: {e}")