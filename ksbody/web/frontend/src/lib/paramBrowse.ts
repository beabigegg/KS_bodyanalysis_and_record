export function formatParamGroupLabel(value: string) {
  const wireMatch = /^wire_(\d+)$/.exec(value)
  if (wireMatch) {
    return `Bond Group ${wireMatch[1]}`
  }
  if (value === 'parms') {
    return 'Param Group 1'
  }
  const parmsMatch = /^parms_(\d+)$/.exec(value)
  if (parmsMatch) {
    return `Param Group ${parmsMatch[1]}`
  }
  return value
}
