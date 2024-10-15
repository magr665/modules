"""
*************** arcgisProPopup
bruger følgende:
    fc --> en featureclass f.eks. GeoData.LemvigVand.Spildevandsledning
    conn --> stien til en databaseconnection
    exclude --> en liste over de felt-aliaser som ikke skal medtages
    showIfEmpty --> en liste over de felt-aliaser som skal vises selv om de er tomme

    returnere et Arcade script som er lige til at sætte in i arcgis pro
    Kan evt. gemmes i en folder og bruges senere

*************** webgisPopup
    bruger det samme som arcgisProPopup samt en title

    returnere et JSON med tilhørende Expressions som kan indsættes via ArcGIS Online Assistant
    Kan evt. gemmes i en folder og bruges senere
    
"""
import arcpy
import os
import json
def arcgisProPopup(fc, conn, exclude=None, showIfEmpty=None):
    popup = """ 
            var attributes = {};
            var fieldInfos = [];
            var fullFeature = getfeatureset($feature);
            var flds = schema(fullFeature)["fields"];
            var show = SHOW_LIST; 
            Var showNotIfEmpty = SHOW_NOT_IF_EMPTY_LIST;
            var rowID = 0;
            for (var f in flds) {
                var fieldname = flds[f]["alias"];
                var fieldvalue = $feature[flds[f]["name"]];
                if (!includes(showNotIfEmpty, fieldname) && isEmpty(fieldvalue)) {fieldvalue = ' '}

                if (includes(show, fieldname) && (!isEmpty(fieldvalue) && fieldvalue != ' ')) {
                    var valType = flds[f]["type"];
                    if (valType == 'esriFieldTypeDate') {
                        fieldvalue = text(fieldvalue, 'DD-MM-Y')
                    };
                    attributes[fieldname] = fieldvalue;
                    var fi = {
                        fieldName: fieldname
                    };
                    insert(fieldInfos, rowID, fi);
                    rowID = rowID + 1;
                };
            };
            return {
                type: "fields",
                fieldInfos: fieldInfos,
                attributes: attributes
            };
"""
    featureclass = os.path.join(conn, fc)
    desc = arcpy.Describe(featureclass)
    # for field in desc.fields:
    if not exclude: exclude = []
    if not showIfEmpty: showIfEmpty = []
    show = []
    shownotifempty = []
    for field in desc.fields:
        if field.aliasName in exclude: continue
        if field.name.lower().startswith('shape'): continue
        if field.name.lower().startswith('objectid'): continue
        show.append(field.aliasName)
        if field.aliasName in showIfEmpty:
            continue
        else:
            shownotifempty.append(field.aliasName)
    popup = popup.replace('SHOW_LIST', str(show)).replace('SHOW_NOT_IF_EMPTY_LIST', str(shownotifempty))
    return popup

def webgisPopup(fc, conn, title, showIfEmpty=[], exclude=[], showNotIfEmpty=[]):
    featureclass = os.path.join(conn, fc)
    desc = arcpy.Describe(featureclass)
    # for field in desc.fields:
    show = []
    shownotifempty = []
    fieldInfos = []
    expressions = []
    trs = []
    color1 = 'rgb(224,224,224)'
    color2 = 'rgb(255,255,255)'
    border_bottom1 = '#4d4d4d'
    border_bottom2 = '#4d4d4d'
    idx = 0
    for field in desc.fields:

        if field.name.lower().startswith('shape'): continue
        if field.name.lower().startswith('objectid'): continue
        # print(field.name, field.type)
        if field.type == 'String':
            fieldInfos.append({"fieldName": field.name,
                        "label": field.aliasName,
                        "isEditable": False,
                        "visible": True if field.aliasName not in exclude else False,
                        "stringFieldOption": "textbox"})
        elif field.type in ['SmallInteger', 'Integer']:
            fieldInfos.append({
                        "fieldName": field.name,
                        "label": field.aliasName,
                        "isEditable": False,
                        "visible": True if field.aliasName not in exclude else False,
                        "format": {
                            "places": 0,
                            "digitSeparator": False
                        }})
        elif field.type == 'Date':
            fieldInfos.append({
                        "fieldName": field.name,
                        "label": field.aliasName,
                        "isEditable": False,
                        "visible": True if field.aliasName not in exclude else False,
                        "format": {
                            "dateFormat": "shortDateLE"
                        }
                    })
        elif field.type == 'Double':
            fieldInfos.append({
                        "fieldName": field.name,
                        "label": field.aliasName,
                        "isEditable": False,
                        "visible": True if field.aliasName not in exclude else False,
                        "format": {
                            "places": 2,
                            "digitSeparator": True
                        }})
        if field.name == 'xTid':
            expressions.append({
                        "name": field.name,
                        "title": field.aliasName,
                        "returnType": "string",
                        "expression": "var d = Split($feature.xTid, 'T')[0]\nvar dd = Split(d, '-')\nreturn Concatenate(dd[2], '-', dd[1], '-', dd[0])"
                        })
        elif field.aliasName in showNotIfEmpty:
            expressions.append({
                        "name": field.name,
                        "title": field.aliasName,
                        "expression": f"iif(isempty($feature.{field.name}), 'none', '{field.name}')",
                        "returnType": "string"
                        })
        # laver TR
        color = color1 if idx % 2 == 0 else color2
        hidden = "; display: {expression/" + field.name + "}" if field.aliasName in showNotIfEmpty else ''
        trs.append(f"<tr valign='top' style='background-color: {color};border-bottom: 1px solid {border_bottom1}{hidden}'><td style='color: rgb(74, 74, 74);'>{field.aliasName}</td><td style='color: rgb(0,0,0);'>" + '{' + field.name + '}' + "</td></tr>")
        idx += 1
    table = f"""<div><table style='vertical-align: top;width: 100%;background-color: #F7F7F7;border: 1px solid black;border-collapse: collapse;font-family: Segoe UI, Tahoma, Verdana, Geneva, Arial, Helvetica, sans-serif;font-size: 9pt;'>{''.join(trs)}</table></div>""".replace('\n', '\\n')
    # print(table)
    popupInfo = {"title": title,
        "fieldInfos": fieldInfos,
        "description": table,
        "mediaInfos": [],
        "expressionInfos": expressions}

    result = '"popupInfo":' + json.dumps(popupInfo)

    return result #{'fieldInfos': fieldInfos, 'expressions': expressions, 'table': table}


pp = webgisPopup('Administration.AdgangsAdresser', r'Z:\Arcgis Administration\_DatabaseConnections\PortalProd_Administration.sde', 'Adgangsadresse')
print(pp)
