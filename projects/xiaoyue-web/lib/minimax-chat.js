const axios = require('axios');

const MINIMAX_PROVIDER_NAME = 'MiniMax';

const MINIMAX_TEXT_MODEL_CONFIG = {
  reason_codes: {
    provider_add: 'provider-add',
    model_add: 'model-add',
    parameter_refresh: 'parameter-refresh',
    input_capability: 'input-capability',
  },
  model_id: 'MiniMax-M3.1-Flash',
  model_ids: ['MiniMax-M3.1-Flash', 'MiniMax-M3'],
  models: [
    {
      model_id: 'MiniMax-M3.1-Flash',
      context_window: 1000000,
      max_output_tokens: 524288,
      pricing_usd_per_million_tokens: {
        input: 0.15,
        output: 0.60,
        cache_read: 0.015,
        cache_write: null,
      },
      input_modalities: ['text', 'image', 'video'],
      thinking: ['adaptive'],
      reasoning_effort: ['low', 'medium', 'high', 'xhigh', 'max'],
      default_reasoning_effort: 'max',
    },
    {
      model_id: 'MiniMax-M3',
      context_window: 1000000,
      // Standard rates for up to 512k input tokens.
      pricing_usd_per_million_tokens: {
        input: 0.3,
        output: 1.2,
        cache_read: 0.06,
        cache_write: null,
      },
      pricing_above_512k_usd_per_million_tokens: {
        input: 0.6,
        output: 2.4,
        cache_read: 0.12,
        cache_write: null,
      },
      priority_price_multiplier: 1.5,
      input_modalities: ['text', 'image', 'video'],
      thinking: ['adaptive', 'disabled'],
    },
  ],
  anthropic_base_url: 'https://api.minimax.io/anthropic',
  openai_base_url: 'https://api.minimax.io/v1',
  context_window: 1000000,
  max_output_tokens: 524288,
  pricing_usd_per_million_tokens: {
    input: 0.15,
    output: 0.60,
    cache_read: 0.015,
    cache_write: null,
  },
  thinking: ['adaptive'],
};

const MINIMAX_REGIONAL_ENDPOINTS = [
  {
    region: 'global_en',
    openai_base_url: 'https://api.minimax.io/v1',
    anthropic_base_url: 'https://api.minimax.io/anthropic',
    docs_root: 'https://platform.minimax.io/docs',
  },
  {
    region: 'cn_zh',
    openai_base_url: 'https://api.minimaxi.com/v1',
    anthropic_base_url: 'https://api.minimaxi.com/anthropic',
    docs_root: 'https://platform.minimaxi.com/docs',
  },
];

const MINIMAX_REGION_MAP = Object.fromEntries(
  MINIMAX_REGIONAL_ENDPOINTS.map((entry) => [entry.region, entry]),
);

const MINIMAX_MODEL_MAP = Object.fromEntries(
  MINIMAX_TEXT_MODEL_CONFIG.models.map((model) => [model.model_id, model]),
);

function normalizeMiniMaxRegion(region) {
  return region === 'cn_zh' ? 'cn_zh' : 'global_en';
}

function resolveMiniMaxConfig(overrides = {}) {
  const region = normalizeMiniMaxRegion(
    overrides.region || process.env.MINIMAX_REGION || MINIMAX_REGIONAL_ENDPOINTS[0].region,
  );
  const regionConfig = MINIMAX_REGION_MAP[region] || MINIMAX_REGIONAL_ENDPOINTS[0];
  const requestedModelId = overrides.modelId || overrides.model || process.env.MINIMAX_MODEL || MINIMAX_TEXT_MODEL_CONFIG.model_id;
  // The ordinary catalog must not reset explicit legacy or custom model IDs.
  const modelId = requestedModelId;
  const modelSpec = Object.prototype.hasOwnProperty.call(MINIMAX_MODEL_MAP, modelId)
    ? MINIMAX_MODEL_MAP[modelId] : undefined;
  const apiKey = overrides.apiKey || process.env.MINIMAX_API_KEY || '';
  const apiBaseUrl = overrides.apiBaseUrl || process.env.MINIMAX_API_BASE || regionConfig.openai_base_url;
  const anthropicBaseUrl = overrides.anthropicBaseUrl || process.env.MINIMAX_ANTHROPIC_BASE_URL || regionConfig.anthropic_base_url;

  return {
    providerName: MINIMAX_PROVIDER_NAME,
    apiKey,
    apiBaseUrl,
    anthropicBaseUrl,
    region,
    modelId,
    modelSpec,
    modelIds: MINIMAX_TEXT_MODEL_CONFIG.model_ids.slice(),
    textModelConfig: MINIMAX_TEXT_MODEL_CONFIG,
    regionalEndpoints: MINIMAX_REGIONAL_ENDPOINTS,
  };
}

async function postMiniMaxChatCompletion(options = {}) {
  const config = resolveMiniMaxConfig(options);

  if (!config.apiKey) {
    const error = new Error('MiniMax API key is not configured');
    error.code = 'MINIMAX_API_KEY_MISSING';
    throw error;
  }

  const payload = {
    model: config.modelId,
    messages: options.messages || [],
  };

  if (options.temperature !== undefined) {
    payload.temperature = options.temperature;
  }
  if (options.top_p !== undefined) {
    payload.top_p = options.top_p;
  }
  if (options.max_tokens !== undefined) {
    payload.max_tokens = options.max_tokens;
  }
  if (options.stream !== undefined) {
    payload.stream = options.stream;
  }

  const response = await axios.post(
    `${config.apiBaseUrl}/chat/completions`,
    payload,
    {
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json',
      },
      timeout: options.timeout ?? 30000,
    },
  );

  return { config, response };
}

module.exports = {
  MINIMAX_PROVIDER_NAME,
  MINIMAX_TEXT_MODEL_CONFIG,
  MINIMAX_REGIONAL_ENDPOINTS,
  resolveMiniMaxConfig,
  postMiniMaxChatCompletion,
};
