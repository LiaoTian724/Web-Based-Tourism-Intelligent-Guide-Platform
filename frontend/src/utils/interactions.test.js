import test from 'node:test'
import assert from 'node:assert/strict'
import { recordDetailView } from './interactions.js'

function transport() {
    const requests = []
    return {
        requests,
        dependencies: {
            getCookie: () => 'sessionid=example; csrftoken=csrf%2Dvalue',
            fetchImpl: async (...args) => {
                requests.push(args)
                return { ok: true }
            }
        }
    }
}

test('authenticated detail views send only the target and view action with CSRF', async () => {
    for (const targetType of ['attraction', 'listing']) {
        const { requests, dependencies } = transport()
        assert.equal(await recordDetailView({
            account: { authenticated: true, id: 42 }, targetType, targetId: 7
        }, dependencies), true)
        assert.equal(requests.length, 1)
        const [url, options] = requests[0]
        assert.equal(url, '/api/interactions/')
        assert.equal(options.method, 'POST')
        assert.equal(options.credentials, 'same-origin')
        assert.equal(options.headers['X-CSRFToken'], 'csrf-value')
        assert.equal(options.headers['Content-Type'], 'application/json')
        assert.deepEqual(JSON.parse(options.body), {
            target_type: targetType, target_id: 7, action: 'view'
        })
    }
})

test('anonymous and unresolved account states never send an interaction', async () => {
    const { requests, dependencies } = transport()
    for (const account of [null, undefined, { authenticated: false }, {}]) {
        assert.equal(await recordDetailView({
            account, targetType: 'attraction', targetId: 7
        }, dependencies), false)
    }
    assert.equal(requests.length, 0)
})

test('a detail click can await the current account lookup without recording before login is known', async () => {
    const { requests, dependencies } = transport()
    let resolveAccount
    const account = new Promise(resolve => { resolveAccount = resolve })
    const result = recordDetailView({ account, targetType: 'listing', targetId: 7 }, dependencies)
    await Promise.resolve()
    assert.equal(requests.length, 0)
    resolveAccount({ authenticated: true })
    assert.equal(await result, true)
    assert.equal(requests.length, 1)
})

test('an anonymous result or failed account lookup discards the detail event', async () => {
    const { requests, dependencies } = transport()
    for (const account of [
        Promise.resolve({ authenticated: false }),
        Promise.reject(new Error('account unavailable'))
    ]) {
        assert.equal(await recordDetailView({
            account, targetType: 'listing', targetId: 7
        }, dependencies), false)
    }
    assert.equal(requests.length, 0)
})

test('missing CSRF and invalid targets do not send requests', async () => {
    const { requests, dependencies } = transport()
    const event = { account: { authenticated: true }, targetType: 'attraction', targetId: 7 }
    assert.equal(await recordDetailView(event, { ...dependencies, getCookie: () => '' }), false)
    assert.equal(await recordDetailView({ ...event, targetType: 'user' }, dependencies), false)
    for (const targetId of [0, -1, 1.5, '7', null]) {
        assert.equal(await recordDetailView({ ...event, targetId }, dependencies), false)
    }
    assert.equal(requests.length, 0)
})

test('recording failures resolve quietly and do not retry', async () => {
    const event = { account: { authenticated: true }, targetType: 'listing', targetId: 7 }
    for (const fail of [() => ({ ok: false }), () => { throw new Error('offline') }]) {
        let attempts = 0
        assert.equal(await recordDetailView(event, {
            getCookie: () => 'csrftoken=token',
            fetchImpl: async () => { attempts++; return fail() }
        }), false)
        assert.equal(attempts, 1)
    }
})
