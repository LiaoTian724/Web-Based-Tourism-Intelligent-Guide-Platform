// Called only by explicit detail-opening actions. Failed requests are not retried.
export async function recordDetailView(
    { account, targetType, targetId },
    { fetchImpl = globalThis.fetch, getCookie = () => globalThis.document?.cookie || '' } = {}
) {
    try {
        const currentAccount = await account
        if (currentAccount?.authenticated !== true) return false
        if (!['attraction', 'listing'].includes(targetType)) return false
        if (!Number.isSafeInteger(targetId) || targetId <= 0) return false

        const cookie = getCookie().match(/(?:^|;\s*)csrftoken=([^;]*)/)
        const csrfToken = cookie ? decodeURIComponent(cookie[1]) : ''
        if (!csrfToken) return false

        const response = await fetchImpl('/api/interactions/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ target_type: targetType, target_id: targetId, action: 'view' })
        })
        return response.ok
    } catch {
        // Browsing remains available when account lookup or recording fails.
        return false
    }
}
