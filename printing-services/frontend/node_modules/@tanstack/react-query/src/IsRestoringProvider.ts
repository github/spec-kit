'use client'
import * as React from 'react'

const IsRestoringContext = React.createContext(false)

export const useIsRestoring = () => React.useContext(IsRestoringContext)
export const IsRestoringProvider = IsRestoringContext.Provider
