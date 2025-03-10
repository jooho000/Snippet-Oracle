$(".code-editor")
  .on("keydown", (event) => {
    const textArea = event.target;
    if (event.key === "Tab") {
      let code = textArea.value;
      let start = textArea.selectionStart;
      let end = textArea.selectionEnd;
      [code, start, end] = (event.shiftKey ? unindent : indent)(
        code,
        start,
        end
      );
      textArea.value = code;
      textArea.selectionStart = start;
      textArea.selectionEnd = end;
      event.preventDefault();
    }
  })
  .on("input", (event) => {
    event.target.value = event.target.value.replace("\r\n", "\n");
  });

/**
 * Adds one level of indentation to a string.
 * @param {string} code
 * @param {number | undefined} start
 * @param {number | undefined} end
 */
function indent(code, start, end) {
  if (!start) start = 0;
  if (!end) end = start;

  const lineStart = code.lastIndexOf("\n", start) + 1;
  const ind = "    ";

  if (start === end) {
    // No highlight
    code = code.substring(0, start) + ind + code.substring(start);
    start += 4;
    end += 4;
  } else {
    // Multi-line highlight
    const oldInner = code.substring(lineStart, end);
    const inner = oldInner.replace(/^/gm, ind);
    code = code.substring(0, lineStart) + inner + code.substring(end);
    start += 4;
    end += inner.length - oldInner.length;
  }

  return [code, start, end];
}

/**
 * Removes one level of indentation from a string.
 * @param {string} code
 * @param {number | undefined} start
 * @param {number | undefined} end
 */
function unindent(code, start, end) {
  if (!start) start = 0;
  if (!end) end = start;

  if (start === end && (code[start - 1] === " " || code[start - 1] === "\t")) {
    // No highlight
    const oldInner = code.substring(0, start);
    const inner = oldInner.replace(/ {1,4}$/, "");
    code = inner + code.substring(start);
    start += inner.length - oldInner.length;
    end += inner.length - oldInner.length;
  } else {
    // Multi-line highlight
    const lineStart = Math.max(code.lastIndexOf("\n", start), 0);
    const oldInner = code.substring(lineStart, end);
    let inner = oldInner.replace(/^( {1,4}|\t)/gm, "");
    code = code.substring(0, lineStart) + inner + code.substring(end);
    start = lineStart;
    end += inner.length - oldInner.length;
  }

  return [code, start, end];
}
