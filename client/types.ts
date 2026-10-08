namespace GQ {
  export type Mode = 'practice' | 'live' | 'guided';
  export type Surface = 'uncoated_glass' | 'glazed_ceramic' | 'stainless_steel' | 'glass_ceramic_hob' | 'natural_stone' | 'wood' | 'unknown';
  export type Soil = 'grease' | 'fingerprints' | 'light_grime' | 'limescale' | 'unknown';
  export type Phase = 'identified' | 'confirmed' | 'equipped' | 'cleaning' | 'result';
  export type ResultStatus = 'clear' | 'partial' | 'unverifiable';
  export interface Product {
    id: string; name: string; variant: string; category: string; color: string;
    surfaces: string[]; soils: string[]; excluded: string[]; source: string;
    source_title: string; evidence_summary: string; steps: string[]; restrictions: string[]; enabled: boolean;
  }
  export interface Attestations {
    exact_product: boolean; label_allows_target: boolean; surface_care_allows: boolean;
    no_other_product: boolean; cool_and_safe: boolean;
  }
  export interface Match {
    status: 'eligible' | 'uncertain' | 'blocked'; code: string; reason: string;
    product_id: string; source?: string; steps?: string[];
  }
  export interface Analysis {
    object_name: string; surface: Surface; soil: Soil; visible_soil: boolean;
    image_quality: 'usable' | 'unusable'; material_certainty: 'tentative' | 'unknown'; hazards: string[];
    target_box: {x: number; y: number; width: number; height: number};
  }
  export interface Quest {
    id: string; mode: Mode; phase: Phase; name: string; room: string; before: string;
    after?: string; analysis: Analysis; surface: Surface; soil: Soil;
    productId?: string; targetTicket?: string; encounterTicket?: string;
    scenario?: string; result?: Result;
  }
  export interface Result {
    encounter_id: string; status: ResultStatus; xp: number; reason: string;
    provenance: 'practice_fixture' | 'model_observation' | 'deterministic_guard' | 'self_attested'; receipt?: string;
  }
  export interface InventoryItem {id: string; name: string; catalogId: string | null; note: string; addedAt: string}
  export interface HistoryItem {
    id: string; name: string; room: string; mode: Mode; status: ResultStatus;
    xp: number; date: string; receipt?: string;
  }
  export interface Store {
    version: 1; history: HistoryItem[]; inventory: InventoryItem[];
    active: { product: string; startedAt: string } | null;
  }
  export interface Health {label_ocr_ready?: boolean; live_ready: boolean; provider_host: string | null; provider_model: string | null; version: string; max_calls_hour: number; max_calls_day: number; access_mode: 'private_code' | 'public_rate_limited'; source_sha?: string; deployment_id?: string; replica_region?: string}
  export interface Scenario {
    id: string; name: string; room: string; subtitle: string; surface: Surface; soil: Soil;
    color: string; before: string; after: string; partial: string;
  }
}
