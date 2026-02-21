import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

describe('LoadingSpinner', () => {
  it('renders spinner element', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.spinner').exists()).toBe(true)
  })

  it('does not show message by default', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.loading-message').exists()).toBe(false)
  })

  it('shows message when provided', () => {
    const wrapper = mount(LoadingSpinner, {
      props: { message: 'Loading recipes...' },
    })
    const msg = wrapper.find('.loading-message')
    expect(msg.exists()).toBe(true)
    expect(msg.text()).toBe('Loading recipes...')
  })

  it('applies default size when not specified', () => {
    const wrapper = mount(LoadingSpinner)
    const spinner = wrapper.find('.spinner')
    expect(spinner.attributes('style')).toContain('40px')
  })

  it('applies custom size', () => {
    const wrapper = mount(LoadingSpinner, {
      props: { size: '60px' },
    })
    const spinner = wrapper.find('.spinner')
    expect(spinner.attributes('style')).toContain('60px')
  })

  it('renders loading container', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.loading-container').exists()).toBe(true)
  })
})
