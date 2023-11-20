const contextmenu = document.getElementById('context-menu');
const scope = document.getElementById('map');
const lastclickposition = document.getElementById('lastclickedposition');

const normalize = (mouseX, mouseY) => {

    let {
        left: scopeOffsetX,
        top: scopeOffsetY
    } = scope.getBoundingClientRect();

    scopeOffsetX = scopeOffsetX < 0 ? 0 : scopeOffsetX;
    scopeOffsetY = scopeOffsetY < 0 ? 0 : scopeOffsetY;

    const scopeX = mouseX - scopeOffsetX;
    const scopeY = mouseY - scopeOffsetY;

    const outOfBoundsOnX =
        scopeX + contextmenu.clientWidth > scope.clientWidth;

    const outOfBoundsOnY =
        scopeY + contextmenu.clientHeight > scope.clientHeight;

    let normalizedX = mouseX;
    let normalizedY = mouseY;

    if (outOfBoundsOnX) {
        normalizedX =
            scopeOffsetX + scope.clientWidth - contextmenu.clientWidth;
    }

    if (outOfBoundsOnY) {
        normalizedY =
            scopeOffsetY + scope.clientHeight - contextmenu.clientHeight;
    }

    return { normalizedX, normalizedY };
}

scope.addEventListener('contextmenu', (event) => {
    event.preventDefault();

    const { clientX: mouseX, clientY: mouseY } = event;

    const { normalizedX, normalizedY } = normalize(mouseX, mouseY);

    contextmenu.classList.remove('visible');

    contextmenu.style.top = `${normalizedY}px`;
    contextmenu.style.left = `${normalizedX}px`;

    setTimeout(() => {
        contextmenu.classList.add('visible');
    });
});

scope.addEventListener('click', (e) => {
    if (e.target.offsetParent != contextmenu) {
        contextmenu.classList.remove('visible');
    }
});
