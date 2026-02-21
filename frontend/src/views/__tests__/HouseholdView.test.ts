import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import HouseholdView from '@/views/HouseholdView.vue'

vi.mock('@/services/api', () => ({
  householdApi: {
    get: vi.fn().mockImplementation(() =>
      Promise.resolve({
        data: { id: 'h1', name: 'Test Kitchen', owner_id: 'u1', created_at: '' },
      }),
    ),
    getMembers: vi.fn().mockImplementation(() =>
      Promise.resolve({
        data: [
          { id: 'fm1', household_id: 'h1', user_id: 'u1', name: 'Owner', role: 'owner', dietary_notes: 'Vegan', created_at: '' },
          { id: 'fm2', household_id: 'h1', user_id: null, name: 'Child', role: 'child', dietary_notes: null, created_at: '' },
        ],
      }),
    ),
    addMember: vi.fn().mockImplementation(() =>
      Promise.resolve({
        data: { id: 'fm3', household_id: 'h1', user_id: null, name: 'New Member', role: 'member', dietary_notes: null, created_at: '' },
      }),
    ),
    removeMember: vi.fn().mockResolvedValue({}),
    create: vi.fn(),
    updateMember: vi.fn(),
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/household', name: 'household', component: { template: '<div/>' } }],
})

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(HouseholdView, {
    global: { plugins: [pinia, router] },
  })
}

describe('HouseholdView', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/household')
    await router.isReady()
  })

  it('renders heading', () => {
    const wrapper = mountView()
    expect(wrapper.find('h1').text()).toBe('My Household')
  })

  it('fetches household data on mount', async () => {
    mountView()
    await flushPromises()
    const { householdApi } = await import('@/services/api')
    expect(householdApi.get).toHaveBeenCalled()
    expect(householdApi.getMembers).toHaveBeenCalled()
  })

  it('renders household name', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Test Kitchen')
  })

  it('renders family members', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Owner')
    expect(wrapper.text()).toContain('Child')
  })

  it('renders add member form', () => {
    const wrapper = mountView()
    expect(wrapper.find('#memberName').exists()).toBe(true)
    expect(wrapper.find('#memberRole').exists()).toBe(true)
  })

  it('shows dietary notes for members', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Vegan')
  })

  it('shows remove button for non-owner members', async () => {
    const wrapper = mountView()
    await flushPromises()
    const removeButtons = wrapper.findAll('.remove-btn')
    expect(removeButtons.length).toBe(1)
  })

  it('submits add member form and displays new member', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#memberName').setValue('New Member')
    await wrapper.find('#memberRole').setValue('member')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { householdApi } = await import('@/services/api')
    expect(householdApi.addMember).toHaveBeenCalledWith({
      name: 'New Member',
      role: 'member',
      dietary_notes: undefined,
    })

    // The new member should appear in the list
    expect(wrapper.text()).toContain('New Member')
    // Member count should be updated (3 total: Owner + Child + New Member)
    expect(wrapper.text()).toContain('Family Members (3)')
  })

  it('submits add member form with dietary notes', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#memberName').setValue('Grandma')
    await wrapper.find('#memberRole').setValue('parent')
    await wrapper.find('#dietaryNotes').setValue('Gluten free')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { householdApi } = await import('@/services/api')
    expect(householdApi.addMember).toHaveBeenCalledWith({
      name: 'Grandma',
      role: 'parent',
      dietary_notes: 'Gluten free',
    })
  })

  it('does not add member when name is empty', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#memberName').setValue('   ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const { householdApi } = await import('@/services/api')
    expect(householdApi.addMember).not.toHaveBeenCalled()
  })

  it('clicks remove button and removes non-owner member', async () => {
    const wrapper = mountView()
    await flushPromises()

    // Verify Child is displayed before removal
    expect(wrapper.text()).toContain('Child')

    // Click the remove button (only one exists, for the non-owner 'Child')
    const removeBtn = wrapper.find('.remove-btn')
    await removeBtn.trigger('click')
    await flushPromises()

    const { householdApi } = await import('@/services/api')
    expect(householdApi.removeMember).toHaveBeenCalledWith('fm2')

    // Child should be removed from the list
    const memberCards = wrapper.findAll('.member-card')
    const memberTexts = memberCards.map(c => c.text())
    expect(memberTexts.some(t => t.includes('Child'))).toBe(false)
    // Owner should still be present
    expect(memberTexts.some(t => t.includes('Owner'))).toBe(true)
  })

  it('shows error when fetching household data fails', async () => {
    const { householdApi } = await import('@/services/api')
    vi.mocked(householdApi.get).mockRejectedValueOnce(new Error('Network error'))
    vi.mocked(householdApi.getMembers).mockRejectedValueOnce(new Error('Network error'))

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Failed to load household data')
  })

  it('shows error when addMember fails', async () => {
    const { householdApi } = await import('@/services/api')
    vi.mocked(householdApi.addMember).mockRejectedValueOnce(new Error('Server error'))

    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#memberName').setValue('Bad Member')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Failed to add member')
  })

  it('shows error when removeMember fails', async () => {
    const { householdApi } = await import('@/services/api')
    vi.mocked(householdApi.removeMember).mockRejectedValueOnce(new Error('Server error'))

    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('.remove-btn').trigger('click')
    await flushPromises()

    expect(wrapper.find('.error-text').text()).toBe('Failed to remove member')
  })

  it('does not show remove button for owner member', async () => {
    const wrapper = mountView()
    await flushPromises()

    const memberCards = wrapper.findAll('.member-card')
    // Find the owner card
    const ownerCard = memberCards.find(card => card.text().includes('Owner'))
    expect(ownerCard).toBeDefined()
    expect(ownerCard!.find('.remove-btn').exists()).toBe(false)
  })

  it('displays member count in section header', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Family Members (2)')
  })

  it('renders role badges for members', async () => {
    const wrapper = mountView()
    await flushPromises()
    const badges = wrapper.findAll('.role-badge')
    expect(badges.length).toBe(2)
    expect(badges[0].text()).toBe('owner')
    expect(badges[1].text()).toBe('child')
  })

  it('resets form fields after successful member addition', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('#memberName').setValue('New Member')
    await wrapper.find('#memberRole').setValue('child')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // After successful add, form should be reset
    const nameInput = wrapper.find('#memberName').element as HTMLInputElement
    const roleSelect = wrapper.find('#memberRole').element as HTMLSelectElement
    expect(nameInput.value).toBe('')
    expect(roleSelect.value).toBe('member')
  })
})
