"""Capture an explicitly simulated interface walkthrough, never a real-task demo."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from browser.harness import mount,click,confirm,care_checks

def main():
    (ROOT/'evidence').mkdir(exist_ok=True)
    output=ROOT/'evidence'/'walkthrough-frames';output.mkdir(exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    captures=[]
    with sync_playwright() as p:
        executable=os.getenv('GQ_CHROMIUM_EXECUTABLE','/usr/bin/chromium')
        b=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox'])
        page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        errors=mount(page)
        def snap(label):
            page.wait_for_timeout(120);page.evaluate('window.scrollTo(0,0)')
            file=output/f'{len(captures):02d}.png';page.screenshot(path=str(file))
            image=Image.open(file).convert('RGB');draw=ImageDraw.Draw(image)
            draw.rectangle((0,934,1440,1000),fill='#173d32')
            draw.text((24,947),f'GrimeQuest | {label}',font=font,fill='white')
            draw.text((24,974),'ILLUSTRATED PRACTICE WALKTHROUGH — no live AI or physical cleaning is shown',font=font,fill='#d3ef86')
            image.save(file);captures.append(file)
        snap('01 / A camera-first cleaning quest')
        click(page,'practice-first');snap('02 / Confirm the surface, not just its appearance')
        confirm(page);snap('03 / Your owned products become your loadout')
        click(page,'choose-product','method-kitchen-clementine-uk-828');click(page,'prepare');snap('04 / Care checks come before points')
        care_checks(page);click(page,'start-cleaning');snap('05 / Practice outcomes are explicitly simulated')
        click(page,'practice-compare');snap('06 / Separate practice XP and visible before / after')
        click(page,'finish');click(page,'scenario','mystery');confirm(page);snap('07 / Unknown material: no supported match')
        assert not errors,errors;b.close()
    playlist=output/'frames.txt'
    playlist.write_text(''.join(f"file '{p.name}'\nduration 4\n" for p in captures)+f"file '{captures[-1].name}'\n")
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(playlist),'-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','fast','-crf','24','-movflags','+faststart',str(ROOT/'evidence/interface-walkthrough.mp4')],check=True)
    shutil.rmtree(output)
    print('Created a labeled 28-second practice UI walkthrough.')

if __name__=='__main__':main()
