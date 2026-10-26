"""Exact authorized appearance delta: one fill attribute, or existing Windows icon."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/design/brand/e-red-windows-icon-2026-10-26'
BRAND=ROOT/'apps/android/app/src/main/assets/brand'
WIN=ROOT/'apps/windows-ui/assets/brand'
NS={'svg':'http://www.w3.org/2000/svg'}
spec=importlib.util.spec_from_file_location('e_update',ROOT/'scripts/build-e-red-brand.py')
update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


class BrandEUpdateTests(unittest.TestCase):
    def test_original_windows_masters_and_ico_unchanged(self):
        pins=json.loads((DOC/'reference/before-sha256.json').read_text(encoding='utf-8'))
        for name in ('windows-icon.svg','windows-icon.png','windows-icon.ico'):
            self.assertEqual(sha(WIN/name),pins[(WIN/name).relative_to(ROOT).as_posix()])

    def test_only_E_fill_changes_all_other_svg_bytes_preserved(self):
        for name in ('logo-horizontal.svg','logo-header-small.svg','logo-compact.svg','splash-screen.svg'):
            with self.subTest(asset=name):
                old=(DOC/'reference'/name).read_text(encoding='utf-8')
                new=(BRAND/name).read_text(encoding='utf-8')
                self.assertEqual(new,update.red_e(old))
                tree=ET.fromstring(new)
                changed=[p for p in tree.findall('.//svg:path',NS) if p.get('fill')=='#ff153f']
                self.assertEqual(len(changed),1)
                self.assertEqual(changed[0].get('d'),update.E_PATH)
                del changed[0].attrib['fill']
                self.assertEqual(ET.tostring(tree),ET.tostring(ET.fromstring(old)))

    def test_L_O_N_and_subtitle_keep_original_white_styles(self):
        tree=ET.parse(BRAND/'logo-horizontal.svg')
        group=next(n for n in tree.findall('.//svg:g',NS) if n.get('fill')=='url(#wordWhite)')
        self.assertEqual(len(group),4)
        self.assertTrue(all('fill' not in p.attrib for p in list(group)[:3]))
        self.assertEqual(group[3].get('fill'),'#ff153f')
        self.assertIn('stroke="#ededf2"',(BRAND/'logo-horizontal.svg').read_text(encoding='utf-8'))

    def test_official_project_red_is_used(self):
        css=(ROOT/'apps/windows-ui/desktop.css').read_text(encoding='utf-8')
        self.assertIn('--red:'+update.RED,css)

    def test_windows_and_android_headers_equal(self):
        for name in ('logo-horizontal.svg','logo-header-small.svg'):
            self.assertEqual((WIN/name).read_bytes(),(BRAND/name).read_bytes())

    def test_android_icon_is_exact_original_windows_asset(self):
        self.assertEqual((BRAND/'app-icon.svg').read_bytes(),(WIN/'windows-icon.svg').read_bytes())
        self.assertEqual((BRAND/'lone-app-icon.png').read_bytes(),(WIN/'windows-icon.png').read_bytes())

    def test_authorized_change_set_is_only_brand_resources_and_description(self):
        changes=json.loads((DOC/'change-manifest.json').read_text(encoding='utf-8'))['authorizedChanges']
        prefix='apps/android/app/src/main/'
        allowed={prefix+'assets/brand/'+n for n in ('logo-horizontal.svg','logo-header-small.svg','logo-compact.svg','splash-screen.svg','app-icon.svg','lone-app-icon.png','brand-manifest.json','header-small-manifest.json')}
        allowed|={prefix+'res/mipmap-'+d+'/'+n+'.png' for d in ('mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi') for n in ('ic_launcher','ic_launcher_round','ic_lone_foreground')}
        allowed|={prefix+'res/drawable-nodpi/'+n+'.png' for n in ('lone_splash_safe','lone_splash_lockup')}
        allowed|={'apps/windows-ui/assets/brand/'+n for n in ('logo-horizontal.svg','logo-header-small.svg')}
        allowed.add(prefix+'assets/index.html')
        self.assertEqual(set(changes),allowed)
        for name,record in changes.items():
            self.assertEqual(sha(ROOT/name),record['after'])

    def test_asset_update_import_has_no_side_effects(self):
        before=sha(BRAND/'logo-horizontal.svg')
        spec.loader.exec_module(update)
        self.assertEqual(sha(BRAND/'logo-horizontal.svg'),before)

if __name__=='__main__':unittest.main()
