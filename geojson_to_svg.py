"""
Fetch simplified China provinces GeoJSON and convert to SVG path data
for embedding in the policy monitoring dashboard HTML.
"""
import json, sys, urllib.request, math

# Aliyun DataV GeoJSON - well-known simplified China provinces boundary
URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"

print(f"Fetching GeoJSON from {URL} ...")
try:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"Primary URL failed: {e}")
    # Fallback: try longwosion/geojson-map-china
    URL2 = "https://raw.githubusercontent.com/longwosion/geojson-map-china/master/json/province.json"
    print(f"Trying fallback: {URL2} ...")
    req = urllib.request.Request(URL2, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

features = data.get("features", [])
print(f"Found {len(features)} features")

# Province name mapping (GeoJSON adcode/name to our short names)
PROV_MAP = {
    "北京市": "北京", "天津市": "天津", "上海市": "上海", "重庆市": "重庆",
    "河北省": "河北", "山西省": "山西", "辽宁省": "辽宁", "吉林省": "吉林",
    "黑龙江省": "黑龙江", "江苏省": "江苏", "浙江省": "浙江", "安徽省": "安徽",
    "福建省": "福建", "江西省": "江西", "山东省": "山东", "河南省": "河南",
    "湖北省": "湖北", "湖南省": "湖南", "广东省": "广东", "海南省": "海南",
    "四川省": "四川", "贵州省": "贵州", "云南省": "云南", "陕西省": "陕西",
    "甘肃省": "甘肃", "青海省": "青海", "台湾省": "台湾",
    "内蒙古自治区": "内蒙古", "广西壮族自治区": "广西", "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏", "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港", "澳门特别行政区": "澳门",
}

SHORT_MAP = {
    "北京": "京", "天津": "津", "上海": "沪", "重庆": "渝",
    "河北": "冀", "山西": "晋", "辽宁": "辽", "吉林": "吉",
    "黑龙江": "黑", "江苏": "苏", "浙江": "浙", "安徽": "皖",
    "福建": "闽", "江西": "赣", "山东": "鲁", "河南": "豫",
    "湖北": "鄂", "湖南": "湘", "广东": "粤", "海南": "琼",
    "四川": "川", "贵州": "黔", "云南": "滇", "陕西": "陕",
    "甘肃": "甘", "青海": "青", "台湾": "台",
    "内蒙古": "蒙", "广西": "桂", "西藏": "藏",
    "宁夏": "宁", "新疆": "新", "香港": "港", "澳门": "澳",
}

# Coordinate transform (same as in the dashboard)
# x = (lon - 73) * 10, y = (54 - lat) * 11.5
def lon_to_x(lon):
    return (lon - 73) * 10

def lat_to_y(lat):
    return (54 - lat) * 11.5

# Simplify polygon using Ramer-Douglas-Peucker algorithm
def point_line_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

def simplify(points, epsilon):
    if len(points) <= 2:
        return points
    # Find point with max distance from line between first and last
    dmax = 0
    idx = 0
    x1, y1 = points[0]
    x2, y2 = points[-1]
    for i in range(1, len(points) - 1):
        d = point_line_distance(points[i][0], points[i][1], x1, y1, x2, y2)
        if d > dmax:
            dmax = d
            idx = i
    if dmax > epsilon:
        left = simplify(points[:idx + 1], epsilon)
        right = simplify(points[idx:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]

# Convert GeoJSON coordinates to SVG path
def coords_to_svg_path(coords, simplify_eps=0.15):
    """Convert a list of [lon, lat] rings to SVG path data."""
    paths = []
    for ring in coords:
        # Simplify the ring
        simplified = simplify(ring, simplify_eps)
        if len(simplified) < 3:
            continue
        # Convert to SVG coordinates
        svg_points = []
        for lon, lat in simplified:
            x = lon_to_x(lon)
            y = lat_to_y(lat)
            svg_points.append((x, y))
        # Build SVG path
        d = f"M{svg_points[0][0]:.1f},{svg_points[0][1]:.1f}"
        for x, y in svg_points[1:]:
            d += f"L{x:.1f},{y:.1f}"
        d += "Z"
        paths.append(d)
    return " ".join(paths)

# Calculate centroid of a polygon
def polygon_centroid(points):
    cx, cy, area = 0, 0, 0
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        a = x0 * y1 - x1 * y0
        area += a
        cx += (x0 + x1) * a
        cy += (y0 + y1) * a
    area *= 0.5
    if abs(area) < 1e-10:
        # Fallback: simple average
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        return cx, cy
    cx /= (6 * area)
    cy /= (6 * area)
    return cx, cy

# Process features
prov_data = []
for feat in features:
    props = feat.get("properties", {})
    name = props.get("name", "")

    # Skip non-province features (like nine-dash line)
    if name not in PROV_MAP:
        # Try without suffix
        matched = None
        for k, v in PROV_MAP.items():
            if k.startswith(name) or name.startswith(v):
                matched = v
                break
        if not matched:
            print(f"Skipping unknown feature: {name}")
            continue
        prov_name = matched
    else:
        prov_name = PROV_MAP[name]

    geom = feat.get("geometry", {})
    geom_type = geom.get("type", "")
    coordinates = geom.get("coordinates", [])

    # Handle different geometry types
    svg_paths = []
    all_points = []

    if geom_type == "Polygon":
        # coordinates is [ring, ring, ...]
        path = coords_to_svg_path(coordinates)
        if path:
            svg_paths.append(path)
        for ring in coordinates:
            all_points.extend(ring)

    elif geom_type == "MultiPolygon":
        # coordinates is [[ring, ...], [ring, ...], ...]
        for polygon in coordinates:
            path = coords_to_svg_path(polygon)
            if path:
                svg_paths.append(path)
            for ring in polygon:
                all_points.extend(ring)

    if not svg_paths:
        print(f"No valid paths for {prov_name}")
        continue

    # Calculate centroid from all points
    if all_points:
        svg_points = [(lon_to_x(p[0]), lat_to_y(p[1])) for p in all_points]
        cx, cy = polygon_centroid(svg_points)
    else:
        cx, cy = 0, 0

    prov_data.append({
        "name": prov_name,
        "short": SHORT_MAP.get(prov_name, ""),
        "paths": svg_paths,
        "cx": round(cx, 1),
        "cy": round(cy, 1),
        "original_name": name,
        "point_count": len(all_points),
    })

# Sort by our original provMap order for consistency
ORDER = [
    "新疆", "西藏", "青海", "甘肃", "内蒙古", "宁夏", "陕西", "山西", "河北",
    "北京", "天津", "山东", "河南", "湖北", "安徽", "江苏", "上海", "浙江",
    "江西", "福建", "湖南", "四川", "重庆", "贵州", "云南", "广西", "广东",
    "海南", "台湾", "辽宁", "吉林", "黑龙江", "香港", "澳门"
]

def sort_key(p):
    try:
        return ORDER.index(p["name"])
    except ValueError:
        return 999

prov_data.sort(key=sort_key)

# Output
print(f"\nProcessed {len(prov_data)} provinces")
print(f"Total SVG paths: {sum(len(p['paths']) for p in prov_data)}")
print(f"Total points: {sum(p['point_count'] for p in prov_data)}")

# Write JavaScript data to file
with open("C:\\Users\\呼骁\\.qoderwork\\workspace\\mr3bu0bmb7ercsv7\\china_map_paths.js", "w", encoding="utf-8") as f:
    f.write("// China province SVG paths generated from GeoJSON\n")
    f.write("// Transform: x=(lon-73)*10, y=(54-lat)*11.5\n")
    f.write("var provGeoJSON = [\n")
    for p in prov_data:
        paths_str = json.dumps(p["paths"])
        f.write(f'{{n:"{p["name"]}",s:"{p["short"]}",paths:{paths_str},cx:{p["cx"]},cy:{p["cy"]}}},\n')
    f.write("];\n")

print(f"\nOutput written to china_map_paths.js")

# Also output a summary
print("\nProvince summary:")
for p in prov_data:
    print(f"  {p['short']} {p['name']}: {len(p['paths'])} paths, {p['point_count']} pts, centroid ({p['cx']}, {p['cy']})")
