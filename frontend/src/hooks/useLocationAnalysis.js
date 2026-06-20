import { useMutation } from '@tanstack/react-query'
import axios from 'axios'

export function useLocationAnalysis() {
  return useMutation({
    mutationFn: async (params) => {
      const { data } = await axios.post('/api/analyze', params, { timeout: 120000 })
      return data
    },
  })
}
