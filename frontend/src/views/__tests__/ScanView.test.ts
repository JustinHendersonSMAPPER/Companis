import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ScanView from '@/views/ScanView.vue'

vi.mock('@/services/api', () => ({
  ingredientsApi: {
    getHousehold: vi.fn().mockResolvedValue({ data: [] }),
    addToHousehold: vi.fn().mockResolvedValue({
      data: {
        id: 'hi1', household_id: 'h1', ingredient_id: 'i1', quantity: null, unit: null,
        expiry_date: null, source: 'barcode', created_at: '',
        ingredient: { id: 'i1', name: 'Test Product', category: null, barcode: '123', brand: 'Brand', description: null, image_url: null, nutrition_info: null, common_allergens: null, created_at: '' },
      },
    }),
    removeFromHousehold: vi.fn().mockResolvedValue({}),
    scanBarcode: vi.fn().mockResolvedValue({
      data: { found: true, barcode: '123', product_name: 'Test Product', brand: 'Brand', ingredient: null },
    }),
    cameraScan: vi.fn().mockResolvedValue({
      data: { detected_ingredients: ['Tomato', 'Onion'], confidence_scores: { Tomato: 0.95, Onion: 0.8 } },
    }),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/scan', name: 'scan', component: { template: '<div/>' } }],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(ScanView, {
    global: { plugins: [pinia, router] },
  })
}

describe('ScanView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/scan')
    await router.isReady()
  })

  it('renders heading, tabs, and barcode input', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('Scan Ingredients')
    const tabs = wrapper.findAll('.tab')
    expect(tabs.length).toBe(2)
    expect(tabs[0].text()).toContain('Barcode Scanner')
    expect(tabs[1].text()).toContain('Camera Scan')
    expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toContain('Look Up Barcode')
  })

  it('switches to camera tab', async () => {
    const wrapper = mountView()
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')
    expect(wrapper.text()).toContain('Camera Ingredient Detection')
    expect(wrapper.text()).toContain('Start Camera')
    expect(wrapper.find('video').exists()).toBe(true)
  })

  it('submits barcode form and calls store.scanBarcode', async () => {
    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.scanBarcode).toHaveBeenCalledWith('123')
  })

  it('empty barcode does not scan', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.scanBarcode).not.toHaveBeenCalled()
  })

  it('whitespace-only barcode does not scan', async () => {
    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('   ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.scanBarcode).not.toHaveBeenCalled()
  })

  it('handles barcode scan error', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.scanBarcode).mockRejectedValueOnce(new Error('Network error'))

    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('999')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Failed to look up barcode')
  })

  it('shows barcode result when found', async () => {
    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Test Product')
    expect(wrapper.text()).toContain('Brand')
    expect(wrapper.find('.result').exists()).toBe(true)
    expect(wrapper.find('.result .btn-primary').text()).toContain('Add to Pantry')
  })

  it('adds barcode ingredient when clicking Add to Pantry', async () => {
    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const addBtn = wrapper.find('.result .btn-primary')
    await addBtn.trigger('click')
    await flushPromises()

    const { ingredientsApi } = await import('@/services/api')
    expect(ingredientsApi.addToHousehold).toHaveBeenCalledWith({
      name: 'Test Product',
      barcode: '123',
      source: 'barcode',
    })

    // After successful add, result and input should be cleared
    expect(wrapper.find('.result').exists()).toBe(false)
  })

  it('addBarcodeIngredient does nothing when result not found', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.scanBarcode).mockResolvedValueOnce({
      data: { found: false, barcode: '999', product_name: null, brand: null, ingredient: null },
    } as never)

    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('999')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // Result shows "not found"
    expect(wrapper.text()).toContain('Product not found for barcode: 999')

    // No "Add to Pantry" button should be visible for unfound products
    const resultDiv = wrapper.find('.result')
    expect(resultDiv.exists()).toBe(true)
    // The v-if="barcodeResult.found" block does not render the add button
    expect(resultDiv.find('.btn-primary').exists()).toBe(false)
  })

  it('addBarcodeIngredient handles error', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.addToHousehold).mockRejectedValueOnce(new Error('Server error'))

    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const addBtn = wrapper.find('.result .btn-primary')
    await addBtn.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Failed to add ingredient')
  })

  it('camera error when getUserMedia rejects', async () => {
    const originalMediaDevices = navigator.mediaDevices
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn().mockRejectedValue(new Error('Permission denied')),
      },
      configurable: true,
    })

    const wrapper = mountView()
    await flushPromises()

    // Switch to camera tab
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')

    // Click Start Camera
    const startBtn = wrapper.find('.camera-controls .btn-primary')
    expect(startBtn.text()).toContain('Start Camera')
    await startBtn.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not access camera. Please check permissions.')

    Object.defineProperty(navigator, 'mediaDevices', {
      value: originalMediaDevices,
      configurable: true,
    })
  })

  it('adds detected ingredient from camera scan result', async () => {
    const { ingredientsApi } = await import('@/services/api')

    const wrapper = mountView()
    await flushPromises()

    // Switch to camera tab
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')

    // Set cameraResult via component internals since we cannot trigger real camera capture
    const vm = wrapper.vm as unknown as { cameraResult: { detected_ingredients: string[]; confidence_scores: Record<string, number> } | null }
    vm.cameraResult = {
      detected_ingredients: ['Tomato', 'Onion'],
      confidence_scores: { Tomato: 0.95, Onion: 0.8 },
    }
    await wrapper.vm.$nextTick()

    // Detected items should be rendered
    expect(wrapper.text()).toContain('Tomato')
    expect(wrapper.text()).toContain('95% confidence')
    expect(wrapper.text()).toContain('Onion')
    expect(wrapper.text()).toContain('80% confidence')

    // Click "Add" on first detected ingredient
    const addBtns = wrapper.findAll('.detected-item .btn-sm')
    expect(addBtns.length).toBe(2)
    await addBtns[0].trigger('click')
    await flushPromises()

    expect(ingredientsApi.addToHousehold).toHaveBeenCalledWith({
      name: 'Tomato',
      source: 'camera',
    })
  })

  it('addDetectedIngredient handles error', async () => {
    const { ingredientsApi } = await import('@/services/api')
    vi.mocked(ingredientsApi.addToHousehold).mockRejectedValueOnce(new Error('fail'))

    const wrapper = mountView()
    await flushPromises()

    // Switch to camera tab
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')

    const vm = wrapper.vm as unknown as { cameraResult: { detected_ingredients: string[]; confidence_scores: Record<string, number> } | null }
    vm.cameraResult = {
      detected_ingredients: ['Tomato'],
      confidence_scores: { Tomato: 0.9 },
    }
    await wrapper.vm.$nextTick()

    const addBtn = wrapper.findAll('.detected-item .btn-sm')[0]
    await addBtn.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Failed to add Tomato')
  })

  it('stopCamera stops tracks and deactivates camera', async () => {
    const stopFn = vi.fn()

    const wrapper = mountView()
    await flushPromises()

    // Switch to camera tab
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')
    await wrapper.vm.$nextTick()

    // Directly set internal state to simulate camera started
    const vm = wrapper.vm as unknown as { cameraActive: boolean }
    vm.cameraActive = true
    await wrapper.vm.$nextTick()

    // Set up mock srcObject on the actual video element in the DOM
    const videoEl = wrapper.find('video').element as HTMLVideoElement
    const mockStream = { getTracks: () => [{ stop: stopFn }] }
    Object.defineProperty(videoEl, 'srcObject', { value: mockStream, writable: true, configurable: true })

    // Stop Camera button should be visible now
    const stopBtn = wrapper.find('.btn-secondary')
    expect(stopBtn.exists()).toBe(true)
    expect(stopBtn.text()).toContain('Stop Camera')
    await stopBtn.trigger('click')
    await wrapper.vm.$nextTick()

    // Track stop should have been called
    expect(stopFn).toHaveBeenCalled()
    // Camera should be deactivated
    expect(vm.cameraActive).toBe(false)
  })

  it('barcode tab is active by default', () => {
    const wrapper = mountView()
    const tabs = wrapper.findAll('.tab')
    expect(tabs[0].classes()).toContain('active')
    expect(tabs[1].classes()).not.toContain('active')
  })

  it('camera tab becomes active on click', async () => {
    const wrapper = mountView()
    const tabs = wrapper.findAll('.tab')
    await tabs[1].trigger('click')
    expect(tabs[1].classes()).toContain('active')
    expect(tabs[0].classes()).not.toContain('active')
  })

  it('scanning state disables submit button', async () => {
    const { ingredientsApi } = await import('@/services/api')
    // Make scanBarcode take a long time so we can check the scanning state
    let resolveBarcode: (value: unknown) => void
    vi.mocked(ingredientsApi.scanBarcode).mockImplementationOnce(() =>
      new Promise((resolve) => { resolveBarcode = resolve })
    )

    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.find('input[inputmode="numeric"]')
    await input.setValue('123')
    await wrapper.find('form').trigger('submit')
    // Don't flush - we're in scanning state
    await wrapper.vm.$nextTick()

    const submitBtn = wrapper.find('button[type="submit"]')
    expect(submitBtn.attributes('disabled')).toBeDefined()
    expect(submitBtn.text()).toContain('Looking up...')

    // Resolve so test cleans up properly
    resolveBarcode!({ data: { found: true, barcode: '123', product_name: 'Test', brand: null, ingredient: null } })
    await flushPromises()
  })
})
