const CLASSIFICATION_KEYS = ['process_step', 'param_group', 'stage', 'category', 'family', 'feature', 'instance', 'tunable', 'description']

export function getHiddenClassificationKeys(fileType: string): Set<string> {
  if (fileType === 'PRM') {
    return new Set(CLASSIFICATION_KEYS.filter((k) => k !== 'param_group' && k !== 'process_step'))
  }
  if (fileType === 'PHY' || fileType === 'REF') {
    return new Set(CLASSIFICATION_KEYS.filter((k) => k !== 'param_group'))
  }
  return new Set(CLASSIFICATION_KEYS)
}
