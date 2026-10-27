from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path
from uuid import uuid4
import subprocess, json, re, shutil

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
app = FastAPI(title="Dachivo Studio v1")

class Episode(BaseModel):
    title: str = "Lumi and the Lost Cub"
    idea: str
    duration: int = 180
    clip_seconds: int = 8

LOCK = ("Lumi: 6-year-old girl, brown eyes, short wavy dark-brown hair, pastel-yellow shirt, "
        "light-blue overalls, white shoes. Miko: tiny orange fox, white chest and tail tip. "
        "Tano: gray baby elephant, floppy ears. Keep identical anatomy, faces, outfit, "
        "fur color, environment and proportions. Cinematic 3D, no text or morphing. "
        "Continue motion and camera angle from the previous segment. ")
BEATS = [
    "Joyful forest meadow opening: Lumi runs with Miko and Tano.",
    "Playful chase, humorous small stumble, happy expressions.",
    "Lumi hears a frightened whimper near the bushes.",
    "Lumi discovers a lost fox cub with a white forehead patch.",
    "Lumi gently reassures the cub; the friends gather.",
    "The team notices tracks and begins searching.",
    "Miko follows the scent as Lumi carries the cub.",
    "A shallow stream blocks their path.",
    "Tano slips harmlessly; the others help him.",
    "Light rain begins in a shaded forest.",
    "The trail fades; the cub cries for its mother.",
    "Lumi comforts the cub under a large tree.",
    "The group shares a quiet, sad emotional moment.",
    "Miko hears a distant answering fox call.",
    "Hope returns; they resume the search.",
    "They reach a clearing and see the mother fox.",
    "Lumi places the cub gently on the ground.",
    "The cub runs toward its mother.",
    "The mother and cub reunite with affection.",
    "Lumi smiles with relieved happy tears.",
    "The mother and cub leave safely together.",
    "The friends return to their meadow.",
    "Golden sunset, butterfly lands on Lumi's nose, happy ending."
]

def project_path(project_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", project_id):
        raise HTTPException(400, "Invalid project ID")
    folder = DATA / project_id
    if not (folder / "storyboard.json").exists():
        raise HTTPException(404, "Project not found")
    return folder

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dachivo Studio</title>
<style>body{font:16px system-ui;background:#0f1524;color:#f5f7ff;max-width:850px;margin:30px auto;padding:20px}input,textarea,button{box-sizing:border-box;width:100%;padding:14px;margin:9px 0;border-radius:10px;border:1px solid #64748b;background:#18243b;color:white}button{background:#2678ef;border:0;cursor:pointer;font-weight:bold}pre{white-space:pre-wrap;background:#18243b;padding:16px;border-radius:12px;max-height:460px;overflow:auto}a{color:#8ac9ff}</style>
<h1>🎬 Dachivo Studio v1</h1><p>Storyboard → prompt → unggah hasil Google Flow → MP4. Generasi Google Flow masih manual. Output tanpa audio.</p>
<input id="title" value="Lumi and the Lost Cub" placeholder="Judul"><textarea id="idea" rows="4">Lumi menemukan bayi rubah tersesat di hutan lalu membantu mempertemukannya dengan ibunya.</textarea>
<button onclick="create()">Buat storyboard 3 menit</button><pre id="out">Masukkan ide, kemudian buat storyboard.</pre><div id="upload"></div>
<script>
let pid="";
async function create(){
const r=await fetch("/api/episodes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:document.getElementById("title").value,idea:document.getElementById("idea").value})});
const v=await r.json();if(!r.ok){document.getElementById("out").textContent=JSON.stringify(v);return;}
pid=v.id;document.getElementById("out").textContent=v.shots.map(s=>"SHOT "+String(s.number).padStart(2,"0")+" | "+s.start+"–"+s.end+" sec\n"+s.prompt).join("\n\n");
document.getElementById("upload").innerHTML='<h2>Upload klip Google Flow</h2><p>Gunakan nama 001.mp4, 002.mp4, ... sesuai urutan.</p><input type="file" id="files" multiple accept="video/mp4"><button onclick="upload()">Upload klip</button><button onclick="assemble()">Gabungkan MP4</button><p id="status"></p>';
}
async function upload(){
const files=document.getElementById("files").files;
for(const f of files){const fd=new FormData();fd.append("file",f);const r=await fetch("/api/episodes/"+pid+"/clips",{method:"POST",body:fd});if(!r.ok){document.getElementById("status").textContent=await r.text();return;}}
document.getElementById("status").textContent=files.length+" file berhasil diunggah";
}
async function assemble(){
const r=await fetch("/api/episodes/"+pid+"/render",{method:"POST"});const v=await r.json();
document.getElementById("status").textContent="";
if(r.ok){const a=document.createElement("a");a.href=v.download;a.textContent="Unduh MP4 (tanpa audio)";document.getElementById("status").appendChild(a);}
else document.getElementById("status").textContent="Error: "+JSON.stringify(v);
}
</script></html>"""

@app.post("/api/episodes")
def create(ep: Episode):
    if not 60 <= ep.duration <= 180 or ep.clip_seconds not in (8, 10):
        raise HTTPException(400, "Duration must be 60–180 seconds; clip must be 8 or 10 seconds")
    project_id = uuid4().hex[:12]
    folder = DATA / project_id
    (folder / "clips").mkdir(parents=True)
    n = (ep.duration + ep.clip_seconds - 1) // ep.clip_seconds
    shots = []
    for i in range(n):
        beat = BEATS[min(int(i * len(BEATS) / n), len(BEATS) - 1)]
        shots.append({"number": i+1, "start": i*ep.clip_seconds, "end": min((i+1)*ep.clip_seconds, ep.duration),
                      "prompt": f"SHOT {i+1}/{n}. Continue from previous final frame (use frame reference if supported). Story: {ep.idea} Action: {beat} {LOCK} End with a clear movement that carries into the next shot."})
    result = {"id": project_id, "title": ep.title, "idea": ep.idea, "duration": ep.duration, "clip_seconds": ep.clip_seconds, "shots": shots}
    (folder / "storyboard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

@app.post("/api/episodes/{project_id}/clips")
async def upload(project_id: str, file: UploadFile = File(...)):
    folder = project_path(project_id)
    if not re.fullmatch(r"\d{3}\.mp4", file.filename or ""):
        raise HTTPException(400, "Filename must be 001.mp4, 002.mp4, etc.")
    dest = folder / "clips" / file.filename
    with dest.open("wb") as target:
        shutil.copyfileobj(file.file, target)
    return {"saved": dest.name, "bytes": dest.stat().st_size}

@app.post("/api/episodes/{project_id}/render")
def render(project_id: str):
    folder = project_path(project_id)
    files = sorted((folder / "clips").glob("*.mp4"))
    if not files:
        raise HTTPException(400, "Upload your clips first")
    for idx, f in enumerate(files, 1):
        if f.name != f"{idx:03d}.mp4":
            raise HTTPException(400, "Clip numbering is missing or out of order")
    normalized = folder / "normalized"
    normalized.mkdir(exist_ok=True)
    for idx, f in enumerate(files, 1):
        out = normalized / f"{idx:03d}.mp4"
        cmd = ["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(f),"-vf",
               "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p",
               "-c:v","libx264","-preset","veryfast","-crf","22","-an",str(out)]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            raise HTTPException(500, f"FFmpeg failure: {exc}")
        if p.returncode:
            raise HTTPException(500, f"Error processing {f.name}: {p.stderr[-300:]}")
    parts = folder / "parts.txt"
    parts.write_text("".join("file '"+(normalized / f"{i:03d}.mp4").as_posix()+"'\n" for i in range(1,len(files)+1)))
    output = folder / "final.mp4"
    p = subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(parts),"-c","copy","-movflags","+faststart",str(output)],capture_output=True,text=True,timeout=600)
    if p.returncode:
        raise HTTPException(500, p.stderr[-300:])
    return {"download": f"/api/episodes/{project_id}/download", "clips": len(files), "note": "Draft without audio. Duration is not automatically trimmed."}

@app.get("/api/episodes/{project_id}/download")
def download(project_id: str):
    file = project_path(project_id) / "final.mp4"
    if not file.exists():
        raise HTTPException(404, "Render first")
    return FileResponse(file, media_type="video/mp4", filename="Dachivo_Episode.mp4")
