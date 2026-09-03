"""
Update the policy-monitor-dashboard.html:
1. Add month-level CSS for timeline view
2. Replace renderTimeline() to show recent year broken down by month
"""
import re

FILE = r'C:\Users\呼骁\.qoderwork\workspace\mr3bu0bmb7ercsv7\outputs\policy-monitor-dashboard.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. CSS: Replace old timeline styles + add month-level styles
# ============================================================
old_css = """/* Timeline View */
.timeline-item{display:flex;gap:0;margin-bottom:0}
.timeline-year{width:72px;text-align:right;padding:20px 12px 20px 0;font-size:18px;font-weight:800;color:#1E40AF;flex-shrink:0}
.timeline-dot-line{display:flex;flex-direction:column;align-items:center;width:36px;flex-shrink:0}
.timeline-dot{width:14px;height:14px;border-radius:50%;background:#1E40AF;border:3px solid #BFDBFE;flex-shrink:0;margin-top:24px;z-index:2}
.timeline-line{width:2px;background:#CBD5E1;flex:1;margin-top:-2px}
.timeline-item:last-child .timeline-line{display:none}
.timeline-content{flex:1;padding:12px 0 28px 8px}
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}"""

new_css = """/* Timeline View */
.timeline-item{display:flex;gap:0;margin-bottom:0}
.timeline-year{width:72px;text-align:right;padding:20px 12px 20px 0;font-size:18px;font-weight:800;color:#1E40AF;flex-shrink:0}
.timeline-dot-line{display:flex;flex-direction:column;align-items:center;width:36px;flex-shrink:0}
.timeline-dot{width:14px;height:14px;border-radius:50%;background:#1E40AF;border:3px solid #BFDBFE;flex-shrink:0;margin-top:24px;z-index:2}
.timeline-line{width:2px;background:#CBD5E1;flex:1;margin-top:-2px}
.timeline-item:last-child .timeline-line{display:none}
.timeline-content{flex:1;padding:12px 0 28px 8px}
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
/* Month sub-group inside recent year */
.month-group{margin-bottom:20px;position:relative}
.month-group:last-child{margin-bottom:0}
.month-label{display:inline-flex;align-items:center;gap:8px;margin-bottom:10px;padding:4px 14px;background:#EFF6FF;border-radius:20px;font-size:13px;font-weight:700;color:#1E40AF;border:1px solid #BFDBFE}
.month-label .month-count{font-size:11px;font-weight:400;color:#64748B;margin-left:2px}
.timeline-year.expanded{background:linear-gradient(180deg,#EFF6FF 0%,#fff 100%);border-radius:8px 0 0 8px;padding:16px 10px 16px 0}"""

if old_css in content:
    content = content.replace(old_css, new_css)
    print("[OK] CSS updated")
else:
    print("[WARN] Old CSS block not found, trying line-by-line...")

# Also update the responsive CSS for timeline-year
old_resp = "  .timeline-year{width:52px;font-size:15px;padding:14px 6px 14px 0}"
new_resp = "  .timeline-year{width:52px;font-size:15px;padding:14px 6px 14px 0}\n  .month-label{font-size:12px;padding:3px 10px}\n  .month-group{margin-bottom:14px}"
if old_resp in content:
    content = content.replace(old_resp, new_resp)
    print("[OK] Responsive CSS updated")

# ============================================================
# 2. Replace renderTimeline() function
# ============================================================
old_fn = """/* ========== RENDER TIMELINE ========== */
function renderTimeline(){
  var byYear={};
  policies.forEach(function(p){
    var y=p.date.substring(0,4);
    if(!byYear[y])byYear[y]=[];
    byYear[y].push(p);
  });
  var h='';
  Object.keys(byYear).sort().reverse().forEach(function(y){
    h+='<div class="timeline-item">';
    h+='<div class="timeline-year">'+y+'</div>';
    h+='<div class="timeline-dot-line"><div class="timeline-dot"></div><div class="timeline-line"></div></div>';
    h+='<div class="timeline-content"><div class="cards-grid">';
    byYear[y].reverse().forEach(function(p,idx){
      h+=renderPolicyCard(p,idx);
    });
    h+='</div></div></div>';
  });
  document.getElementById('timelineView').innerHTML=h;
}"""

new_fn = r"""/* ========== RENDER TIMELINE ========== */
function renderTimeline(){
  // Find the most recent year among all policies
  var maxYear = 0;
  policies.forEach(function(p){
    var y = parseInt(p.date.substring(0,4), 10);
    if(y > maxYear) maxYear = y;
  });
  var recentYear = String(maxYear);

  // Group policies: recent year -> by month, older years -> by year
  var recentByMonth = {};  // key: "YYYY-MM", value: [policies]
  var byYear = {};         // key: "YYYY", value: [policies]
  policies.forEach(function(p){
    var y = p.date.substring(0,4);
    if(y === recentYear){
      // Extract month: handle "YYYY-MM" and "YYYY-MM-DD" and "YYYY"
      var m = p.date.length >= 7 ? p.date.substring(5,7) : '00';
      var key = y + '-' + m;
      if(!recentByMonth[key]) recentByMonth[key] = [];
      recentByMonth[key].push(p);
    } else {
      if(!byYear[y]) byYear[y] = [];
      byYear[y].push(p);
    }
  });

  var monthNames = {'01':'1月','02':'2月','03':'3月','04':'4月','05':'5月','06':'6月',
                    '07':'7月','08':'8月','09':'9月','10':'10月','11':'11月','12':'12月','00':'其他'};

  var h = '';

  // Render recent year with month breakdown
  if(Object.keys(recentByMonth).length > 0){
    h += '<div class="timeline-item">';
    h += '<div class="timeline-year expanded">' + recentYear + '</div>';
    h += '<div class="timeline-dot-line"><div class="timeline-dot" style="background:#1E40AF;border-color:#93C5FD"></div><div class="timeline-line"></div></div>';
    h += '<div class="timeline-content">';

    // Sort months descending
    var monthKeys = Object.keys(recentByMonth).sort().reverse();
    monthKeys.forEach(function(mk){
      var monthPart = mk.split('-')[1];
      var mName = monthNames[monthPart] || monthPart;
      var items = recentByMonth[mk];
      h += '<div class="month-group">';
      h += '<div class="month-label">' + mName + '<span class="month-count">' + items.length + '条政策</span></div>';
      h += '<div class="cards-grid">';
      items.reverse().forEach(function(p){
        h += renderPolicyCard(p, 0);
      });
      h += '</div></div>';
    });

    h += '</div></div>';
  }

  // Render older years (descending)
  Object.keys(byYear).sort().reverse().forEach(function(y){
    h += '<div class="timeline-item">';
    h += '<div class="timeline-year">' + y + '</div>';
    h += '<div class="timeline-dot-line"><div class="timeline-dot"></div><div class="timeline-line"></div></div>';
    h += '<div class="timeline-content"><div class="cards-grid">';
    byYear[y].reverse().forEach(function(p){
      h += renderPolicyCard(p, 0);
    });
    h += '</div></div></div>';
  });

  document.getElementById('timelineView').innerHTML = h;
}"""

if old_fn in content:
    content = content.replace(old_fn, new_fn)
    print("[OK] renderTimeline() replaced")
else:
    print("[FAIL] Old renderTimeline() not found!")

# ============================================================
# Write back
# ============================================================
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)
print("[OK] File saved")
