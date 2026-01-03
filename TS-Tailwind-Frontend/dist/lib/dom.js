export function el(tag, opts = {}, children = []) {
    const node = document.createElement(tag);
    if (opts.className)
        node.className = opts.className;
    if (opts.text !== undefined)
        node.textContent = opts.text;
    if (opts.attrs) {
        for (const [k, v] of Object.entries(opts.attrs))
            node.setAttribute(k, v);
    }
    for (const child of children)
        node.appendChild(child);
    return node;
}
export function formatDueDate(iso) {
    // Keep it simple & stable: YYYY-MM-DD → e.g. 2025-12-18
    return iso;
}
//# sourceMappingURL=dom.js.map