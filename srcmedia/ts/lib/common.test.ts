import { Component, arraysAreEqual, getTransitionDuration, pluralize } from './common'

describe('Component', () => {

    it('keeps a reference to its element', () => {
        document.body.innerHTML = `<div></div>`
        const element = document.querySelector('div') as HTMLDivElement
        const c = new Component(element)
        expect(c.element).toBe(element)
    })

})

describe('arraysAreEqual', () => {

    it('succeeds if arrays are identical', () => {
        const a = ['a', 1, true]
        const b = ['a', 1, true]
        expect(arraysAreEqual(a, b)).toBe(true)
    })

    it('succeeds if arrays are empty', () => {
        const a = [] as any
        const b = [] as any
        expect(arraysAreEqual(a, b)).toBe(true)
    })

    it('fails if arrays contain different elements', () => {
        const a = ['a', 'b']
        const b = ['a', 'c']
        expect(arraysAreEqual(a, b)).toBe(false)
    })

    it('fails if arrays are different lengths', () => {
        const a = ['a']
        const b = ['a', 'a']
        expect(arraysAreEqual(a, b)).toBe(false)
    })

    it('fails if array elements are different types', () => {
        const a = ['a', 1]
        const b = ['a', '1']
        expect(arraysAreEqual(a, b)).toBe(false)
    })

})

describe('getTransitionDuration', () => {

    beforeEach(() => {
        document.body.innerHTML = `<div id="main-menu"></div>`
    })

    test('uses a transition duration of zero if none is provided', () => {
        let element = document.getElementById('main-menu') as HTMLElement
        expect(getTransitionDuration(element)).toBe(0)
    })

    test('parses and stores a css transition-duration in ms units', () => {
        let element = document.getElementById('main-menu') as HTMLElement
        element.style.transitionDuration = '500ms'
        expect(getTransitionDuration(element)).toBe(500)
    })

    test('parses and stores a css transition-duration in s units', () => {
        let element = document.getElementById('main-menu') as HTMLElement
        element.style.transitionDuration = '1s'
        expect(getTransitionDuration(element)).toBe(1000)
    })

})

describe('pluralize', () => {

    test('return empty string for string "1"', () => {
        expect(pluralize('1')).toBe('')
    })

    test('returns "s" for other strings', () => {
        expect(pluralize('2')).toBe('s')
        expect(pluralize('0')).toBe('s')
        expect(pluralize('-324')).toBe('s')
        expect(pluralize('foo')).toBe('s')
    })

    test('return empty string for number 1', () => {
        expect(pluralize(1)).toBe('')
    })

    test('returns "s" for other numbers', () => {
        expect(pluralize(2)).toBe('s')
        expect(pluralize(0)).toBe('s')
        expect(pluralize(-324)).toBe('s')
    })

    test('return empty string for array of length 1', () => {
        expect(pluralize(['foo'])).toBe('')
    })

    test('returns "s" for other arrays', () => {
        expect(pluralize(['foo', 'bar'])).toBe('s')
        expect(pluralize([])).toBe('s')
    })
})