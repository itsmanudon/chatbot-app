import "@testing-library/jest-dom";

// jsdom doesn't implement scrollIntoView — stub it globally
window.HTMLElement.prototype.scrollIntoView = () => {};
