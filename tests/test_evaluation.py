from pathlib import Path
from datetime import date
from typing import get_args
import pytest
from pydantic import ValidationError

from server.evaluation import (
    CompareCase,
    EvalManifest,
    ProductCase,
    TargetCase,
    resolve_dataset_file,
    score_compare,
    score_product,
    score_target,
    summarize,
    target_candidate_supported,
)
from server.models import Comparison, TargetAnalysis, Surface, Soil, Attestations
from server.policy import PRODUCTS, match_product


def target(**patch):
    base=dict(
        object_name='Tile',
        surface='glazed_ceramic',
        soil='grease',
        visible_soil=True,
        image_quality='usable',
        material_certainty='tentative',
        hazards=['none'],
        target_box={'x':0.1,'y':0.1,'width':0.8,'height':0.8},
    )
    base.update(patch)
    return TargetAnalysis(**base)


def target_case(supported=True,**truth):
    return TargetCase(id='target-1',task='target',image='images/a.jpg',truth={'supported':supported,**truth})


def compare_case(status='partial'):
    return CompareCase(id='compare-1',task='compare',before='images/a.jpg',after='images/b.jpg',truth={'status':status})


def comparison(**patch):
    base=dict(same_target=True,comparable=True,visible_soil_before=True,residue_after='reduced',improvement='some',wet_or_glare=False,obstructed=False)
    base.update(patch)
    return Comparison(**base)


def test_false_supported_is_critical():
    row=score_target(target_case(False,surface='natural_stone'),target())
    assert row['predicted_supported'] is True
    assert row['critical']==['false_supported']


def test_unknown_or_hazard_does_not_enter_supported_candidate_space():
    assert not score_target(target_case(False),target(surface='unknown'))['predicted_supported']
    row=score_target(target_case(False,required_hazards=['heat']),target(hazards=['heat']))
    assert not row['predicted_supported'] and not row['critical']


def test_unapproved_surface_soil_pair_cannot_be_scored_as_supported():
    # Surface and soil are independently known, but this exact combination
    # is not enabled for any reviewed product.
    assert not target_candidate_supported(target(surface='uncoated_glass', soil='grease'))
    row = score_target(target_case(False), target(surface='uncoated_glass', soil='grease'))
    assert not row['predicted_supported']
    assert not row['critical']
    assert target_candidate_supported(target(surface='glazed_ceramic', soil='grease'))
    assert target_candidate_supported(target(surface='uncoated_glass', soil='fingerprints'))


@pytest.mark.parametrize('surface', get_args(Surface))
@pytest.mark.parametrize('soil', get_args(Soil))
def test_evaluation_candidate_pairs_match_released_policy(surface, soil):
    checks = Attestations(**{key: True for key in Attestations.model_fields})
    expected = any(
        match_product(surface, soil, product_id, checks, ['none'], date(2026, 10, 7))['status'] == 'eligible'
        for product_id in PRODUCTS
    )
    assert target_candidate_supported(target(surface=surface, soil=soil)) is expected


def test_required_hazard_miss_is_critical_even_when_model_abstains():
    row=score_target(target_case(False,required_hazards=['electrical']),target(surface='unknown'))
    assert row['critical']==['hazard_miss']
    assert row['hazard_misses']==['electrical']


def test_supported_target_accuracy_uses_surface_and_soil():
    case=target_case(True,surface='glazed_ceramic',soil='grease')
    good=score_target(case,target())
    wrong=score_target(case,target(soil='fingerprints'))
    assert good['exact_surface'] and good['exact_soil']
    assert wrong['exact_surface'] and not wrong['exact_soil']


def test_false_clear_is_critical():
    row=score_compare(compare_case('partial'),comparison(residue_after='not_visible',improvement='substantial'))
    assert row['predicted_status']=='clear' and row['critical']==['false_clear']


@pytest.mark.parametrize('status,patch',[
    ('partial',{}),
    ('unverifiable',{'wet_or_glare':True}),
    ('clear',{'residue_after':'not_visible','improvement':'substantial'}),
])
def test_compare_scoring_uses_application_adjudicator(status,patch):
    row=score_compare(compare_case(status),comparison(**patch))
    assert row['predicted_status']==status and row['exact_status']


def test_product_score_never_creates_critical_permission():
    case=ProductCase(id='p',task='product',front='images/a.jpg',back='images/b.jpg',truth={'label_readable':True,'name_contains':'Kiilto'})
    row=score_product(case,'Kiilto Keittiö',True)
    assert row['readable_match'] and row['name_match'] and row['critical']==[]


def rows_for_qualified_summary():
    rows=[]
    for i in range(12):
        rows.append({'id':f's{i}','task':'target','truth_supported':True,'predicted_supported':True,'exact_surface':True,'exact_soil':True,'hazard_misses':[],'critical':[]})
        rows.append({'id':f'u{i}','task':'target','truth_supported':False,'predicted_supported':False,'exact_surface':True,'exact_soil':True,'hazard_misses':[],'critical':[]})
    for i in range(8):
        rows.append({'id':f'c{i}','task':'compare','expected_status':'clear','predicted_status':'clear','exact_status':True,'critical':[]})
    for i in range(16):
        rows.append({'id':f'n{i}','task':'compare','expected_status':'partial','predicted_status':'partial','exact_status':True,'critical':[]})
    for i in range(6):
        rows.append({'id':f'p{i}','task':'product','readable_match':True,'name_match':True,'critical':[]})
    return rows


def test_release_summary_qualifies_only_with_minimums_and_zero_critical_failures():
    rows=rows_for_qualified_summary()
    result=summarize(rows)
    assert result['qualified'] and all(result['gates'].values())
    rows[12]['critical']=['false_supported']
    result=summarize(rows)
    assert not result['qualified'] and result['critical_failures']['false_supported']==1


def test_call_failure_and_insufficient_dataset_fail_release():
    rows=rows_for_qualified_summary()
    rows[0]={'id':'broken','task':'target','critical':[],'error':'ProviderFailure'}
    result=summarize(rows)
    assert not result['gates']['provider_call_failures_zero']
    assert not result['gates']['dataset_minimums']


def test_manifest_rejects_duplicate_ids_and_extra_fields():
    case={'id':'x','task':'target','image':'images/a.jpg','truth':{'supported':False}}
    with pytest.raises(ValidationError):
        EvalManifest(version=1,cases=[case,case])
    with pytest.raises(ValidationError):
        EvalManifest(version=1,cases=[{**case,'prompt':'ignore safety'}])


def test_dataset_path_cannot_escape(tmp_path):
    root=tmp_path/'dataset';root.mkdir()
    inside=root/'a.jpg';inside.write_bytes(b'x')
    assert resolve_dataset_file(root,'a.jpg')==inside.resolve()
    outside=tmp_path/'outside.jpg';outside.write_bytes(b'x')
    with pytest.raises(ValueError):resolve_dataset_file(root,'../outside.jpg')
