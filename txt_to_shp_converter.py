import shapefile
import os
import sys
import zipfile
from tkinter import filedialog, Tk

def convert_pts_to_shapefiles(pts_path):
    base_dir = os.path.dirname(pts_path)
    base_name = os.path.splitext(os.path.basename(pts_path))[0]

    writers = {
        "polygon": None,
        "polyline": None,
        "point": None,
    }

    feature_ids = {
        "polygon": 1,
        "polyline": 1,
        "point": 1,
    }

    # EPSG:4674 - SIRGAS 2000
    prj_content = """GEOGCS["SIRGAS 2000",
    DATUM["D_SIRGAS_2000",
        SPHEROID["GRS_1980",6378137.0,298.257222101]],
    PRIMEM["Greenwich",0.0],
    UNIT["Degree",0.0174532925199433]]"""

    def get_writer(geom_type):
        if writers[geom_type] is None:
            shp_base = os.path.join(base_dir, f"{base_name}_{geom_type}")
            shape_type = {
                "polygon": shapefile.POLYGON,
                "polyline": shapefile.POLYLINE,
                "point": shapefile.POINT
            }[geom_type]
            writer = shapefile.Writer(shp_base, shapeType=shape_type, encoding='utf-8')
            writer.autoBalance = 1
            writer.field("ID", "N")
            writers[geom_type] = writer
        return writers[geom_type]

    with open(pts_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_type = None
    points = []

    for line in lines:
        line = line.strip()
        if line.startswith("*shpPolygon"):
            current_type = "polygon"
            points = []
        elif line.startswith("*shpPolyline"):
            current_type = "polyline"
            points = []
        elif line.startswith("*shpPoint"):
            current_type = "point"
            points = []
        elif (line == "*" or line == "**") and current_type:
            writer = get_writer(current_type)
            fid = feature_ids[current_type]
            if current_type == "polygon":
                if points:
                    writer.poly([points])
                    writer.record(fid)
                    feature_ids[current_type] += 1
            elif current_type == "polyline":
                if points:
                    writer.line([points])
                    writer.record(fid)
                    feature_ids[current_type] += 1
            elif current_type == "point":
                for pt in points:
                    writer.point(*pt)
                    writer.record(fid)
                    fid += 1
                feature_ids[current_type] = fid
            current_type = None
            points = []
        else:
            try:
                parts = line.split()
                if len(parts) >= 3:
                    x = float(parts[1])
                    y = float(parts[2])
                    points.append([x, y])
            except:
                continue

    # Finaliza e compacta shapefiles
    for geom_type, writer in writers.items():
        if writer:
            shp_base = os.path.join(base_dir, f"{base_name}_{geom_type}")
            writer.close()

            # Cria .prj
            prj_path = shp_base + ".prj"
            with open(prj_path, "w", encoding="utf-8") as f:
                f.write(prj_content)

            # Cria .zip
            zip_path = shp_base + ".zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for ext in [".shp", ".shx", ".dbf", ".prj"]:
                    file_path = shp_base + ext
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))

def run_gui():
    Tk().withdraw()
    pts_path = filedialog.askopenfilename(
        title="Selecione o arquivo .PTS ou .TXT",
        filetypes=[("Arquivos PTS ou TXT", "*.pts *.txt")]
    )
    if pts_path:
        convert_pts_to_shapefiles(pts_path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        convert_pts_to_shapefiles(sys.argv[1])
    else:
        run_gui()
