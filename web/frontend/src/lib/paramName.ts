export function displayParamName(paramName: string, fileType?: string | null) {
  if ((fileType ?? '').toUpperCase() !== 'PRM') {
    return paramName
  }
  const slashIndex = paramName.indexOf('/')
  if (slashIndex < 0) {
    return paramName
  }
  return paramName.slice(slashIndex + 1)
}

export function prmSegmentGroup(paramName: string, fileType?: string | null) {
  if ((fileType ?? '').toUpperCase() !== 'PRM') {
    return null
  }
  const displayName = displayParamName(paramName, fileType)
  const match = /_Seg_(\d+)/i.exec(displayName)
  if (!match) {
    return 'General'
  }
  return `Seg ${match[1].padStart(2, '0')}`
}
