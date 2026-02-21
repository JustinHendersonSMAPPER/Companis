import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import VoiceInput from '@/components/common/VoiceInput.vue'

describe('VoiceInput', () => {
  let origSR: typeof window.SpeechRecognition
  let origWebkit: typeof window.webkitSpeechRecognition

  beforeEach(() => {
    vi.clearAllMocks()
    origSR = window.SpeechRecognition
    origWebkit = window.webkitSpeechRecognition
  })

  afterEach(() => {
    window.SpeechRecognition = origSR
    window.webkitSpeechRecognition = origWebkit
  })

  it('renders voice button', () => {
    const wrapper = mount(VoiceInput)
    expect(wrapper.find('.voice-btn').exists()).toBe(true)
    expect(wrapper.find('.voice-btn').text()).toBe('Voice')
  })

  it('shows error when speech recognition not supported', async () => {
    // @ts-expect-error - deleting browser API for test
    delete window.SpeechRecognition
    // @ts-expect-error - deleting browser API for test
    delete window.webkitSpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')

    expect(wrapper.find('.error-text').text()).toContain('not supported')
  })

  it('does not show transcript by default', () => {
    const wrapper = mount(VoiceInput)
    expect(wrapper.find('.transcript').exists()).toBe(false)
  })

  it('does not show error by default', () => {
    const wrapper = mount(VoiceInput)
    expect(wrapper.find('.error-text').exists()).toBe(false)
  })

  it('has listening class when active and shows Stop', async () => {
    class MockSpeechRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult = null
      onerror = null
      onend: (() => void) | null = null
      start() {
        if (this.onstart) this.onstart()
      }
      stop() {
        if (this.onend) this.onend()
      }
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.voice-btn').classes()).toContain('listening')
    expect(wrapper.find('.voice-btn').text()).toBe('Stop')
  })

  it('stops listening when stop button clicked', async () => {
    const stopFn = vi.fn()

    class MockSpeechRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult = null
      onerror = null
      onend: (() => void) | null = null
      start() {
        if (this.onstart) this.onstart()
      }
      stop() {
        stopFn()
        if (this.onend) this.onend()
      }
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)

    // Start listening
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.voice-btn').text()).toBe('Stop')

    // Stop listening
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    expect(stopFn).toHaveBeenCalled()
    expect(wrapper.find('.voice-btn').text()).toBe('Voice')
    expect(wrapper.find('.voice-btn').classes()).not.toContain('listening')
  })

  it('handles speech recognition result with final transcript', async () => {
    let capturedOnresult: ((event: unknown) => void) | null = null

    class MockSpeechRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult: ((event: unknown) => void) | null = null
      onerror = null
      onend = null
      start() {
        if (this.onstart) this.onstart()
        capturedOnresult = this.onresult
      }
      stop() {}
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    // Simulate a final result
    const mockEvent = {
      resultIndex: 0,
      results: {
        length: 1,
        0: {
          isFinal: true,
          0: { transcript: 'hello world' },
          length: 1,
        },
      },
    }

    capturedOnresult!(mockEvent)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.transcript').text()).toBe('hello world')
    expect(wrapper.emitted('transcript')).toBeTruthy()
    expect(wrapper.emitted('transcript')![0]).toEqual(['hello world'])
  })

  it('handles interim speech recognition results', async () => {
    let capturedOnresult: ((event: unknown) => void) | null = null

    class MockSpeechRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult: ((event: unknown) => void) | null = null
      onerror = null
      onend = null
      start() {
        if (this.onstart) this.onstart()
        capturedOnresult = this.onresult
      }
      stop() {}
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    // Simulate an interim result
    const mockEvent = {
      resultIndex: 0,
      results: {
        length: 1,
        0: {
          isFinal: false,
          0: { transcript: 'hel' },
          length: 1,
        },
      },
    }

    capturedOnresult!(mockEvent)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.transcript').text()).toBe('hel')
    // Interim result should NOT emit transcript
    expect(wrapper.emitted('transcript')).toBeFalsy()
  })

  it('handles speech recognition error', async () => {
    let capturedOnerror: ((event: unknown) => void) | null = null

    class MockSpeechRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult = null
      onerror: ((event: unknown) => void) | null = null
      onend = null
      start() {
        if (this.onstart) this.onstart()
        capturedOnerror = this.onerror
      }
      stop() {}
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.voice-btn').classes()).toContain('listening')

    // Simulate an error
    capturedOnerror!({ error: 'no-speech' })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-text').text()).toContain('no-speech')
    expect(wrapper.find('.voice-btn').classes()).not.toContain('listening')
  })

  it('handles onend callback', async () => {
    let capturedOnend: (() => void) | null = null

    class MockSpeechRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult = null
      onerror = null
      onend: (() => void) | null = null
      start() {
        if (this.onstart) this.onstart()
        capturedOnend = this.onend
      }
      stop() {}
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.voice-btn').classes()).toContain('listening')

    // Trigger onend
    capturedOnend!()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.voice-btn').classes()).not.toContain('listening')
    expect(wrapper.find('.voice-btn').text()).toBe('Voice')
  })

  it('uses webkitSpeechRecognition as fallback', async () => {
    // @ts-expect-error - deleting browser API for test
    delete window.SpeechRecognition

    class MockWebkitSR {
      continuous = false
      interimResults = false
      lang = ''
      onstart: (() => void) | null = null
      onresult = null
      onerror = null
      onend = null
      start() {
        if (this.onstart) this.onstart()
      }
      stop() {}
    }

    window.webkitSpeechRecognition = MockWebkitSR as unknown as typeof SpeechRecognition

    const wrapper = mount(VoiceInput)
    await wrapper.find('.voice-btn').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.voice-btn').classes()).toContain('listening')
  })
})
