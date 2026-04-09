(() => {
  const editor = document.getElementById("rteEditor");
  const contentField = document.getElementById("contentField");
  const insertImageBtn = document.getElementById("insertImageBtn");
  const inlineImagePicker = document.getElementById("inlineImagePicker");
  const uploadList = document.getElementById("inlineUploadList");
  const toastContainer = document.querySelector(".toast-container");

  if (!editor || !contentField) {
    return;
  }

  const inlineUploadUrl = "/api/inline-images";
  const maxWidth = 1600;
  const maxHeight = 1600;
  const jpegQuality = 0.85;
  let pendingUploads = 0;

  const showToast = (message, variant) => {
    if (!toastContainer) {
      return;
    }
    const bg = variant === "success" ? "success" : "danger";
    const icon = variant === "success" ? "check-circle-fill" : "exclamation-triangle-fill";
    const el = document.createElement("div");
    el.className = `toast align-items-center text-white bg-${bg} border-0 shadow-lg`;
    el.role = "alert";
    el.ariaLive = "assertive";
    el.ariaAtomic = "true";
    el.dataset.bsDelay = "5000";
    el.innerHTML = `
      <div class="d-flex">
        <div class="toast-body fs-6">
          <i class="bi bi-${icon} me-2"></i>${escapeHtml(message)}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;
    toastContainer.appendChild(el);
    const toast = new bootstrap.Toast(el);
    el.addEventListener("hidden.bs.toast", function () {
      this.remove();
    });
    toast.show();
  };

  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const setPlaceholder = () => {
    if (editor.innerHTML === "<br>" || editor.innerHTML === "&nbsp;" || editor.innerHTML.trim() === "") {
      editor.classList.add("is-empty");
    } else {
      editor.classList.remove("is-empty");
    }
  };

  const getEditorHtml = () => {
    const raw = editor.innerHTML || "";
    const trimmed = raw.replace(/\u00a0/g, " ").trim();
    if (!trimmed || trimmed === "<br>") return "";
    if (trimmed === "<div><br></div>") return "";
    if (trimmed === "<p><br></p>") return "";
    return raw;
  };

  const syncToHiddenField = () => {
    contentField.value = getEditorHtml();
  };

  const insertNodeAtCursor = (node) => {
    const sel = window.getSelection?.();
    if (!sel || sel.rangeCount === 0) {
      editor.appendChild(node);
      return;
    }
    const range = sel.getRangeAt(0);
    range.deleteContents();
    range.insertNode(node);
    range.setStartAfter(node);
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);
  };

  const compressImage = async (file) => {
    if (!file || !file.type || !file.type.startsWith("image/")) return file;
    if (file.type === "image/gif") return file;

    let bitmap;
    try {
      bitmap = await loadImageBitmap(file);
    } catch (_) {
      return file;
    }
    const srcW = bitmap.width || 0;
    const srcH = bitmap.height || 0;
    if (!srcW || !srcH) return file;

    const scale = Math.min(1, maxWidth / srcW, maxHeight / srcH);
    const dstW = Math.max(1, Math.round(srcW * scale));
    const dstH = Math.max(1, Math.round(srcH * scale));
    if (scale === 1 && file.size <= 900 * 1024 && (file.type === "image/jpeg" || file.type === "image/png")) return file;

    const canvas = document.createElement("canvas");
    canvas.width = dstW;
    canvas.height = dstH;
    const ctx = canvas.getContext("2d", { alpha: true });
    ctx.drawImage(bitmap, 0, 0, dstW, dstH);

    const preferPng = file.type === "image/png";
    const outType = preferPng ? "image/png" : "image/jpeg";
    const blob = await canvasToBlob(canvas, outType, outType === "image/jpeg" ? jpegQuality : undefined);
    const ext = outType === "image/png" ? "png" : "jpg";
    return new File([blob], `image.${ext}`, { type: outType });
  };

  const loadImageBitmap = async (file) => {
    if (window.createImageBitmap) {
      try {
        return await window.createImageBitmap(file);
      } catch (_) {}
    }
    const url = URL.createObjectURL(file);
    try {
      const img = await new Promise((resolve, reject) => {
        const i = new Image();
        i.onload = () => resolve(i);
        i.onerror = reject;
        i.src = url;
      });
      return img;
    } finally {
      URL.revokeObjectURL(url);
    }
  };

  const canvasToBlob = (canvas, type, quality) =>
    new Promise((resolve, reject) => {
      if (canvas.toBlob) {
        canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob failed"))), type, quality);
        return;
      }
      try {
        const dataUrl = canvas.toDataURL(type, quality);
        fetch(dataUrl)
          .then((r) => r.blob())
          .then(resolve, reject);
      } catch (e) {
        reject(e);
      }
    });

  const ensureUploadListVisible = () => {
    if (!uploadList) return;
    uploadList.classList.remove("d-none");
  };

  const createUploadRow = (fileName) => {
    if (!uploadList) return null;
    ensureUploadListVisible();
    const row = document.createElement("div");
    row.className = "inline-upload-row";
    row.innerHTML = `
      <div class="inline-upload-meta">
        <span class="inline-upload-name">${escapeHtml(fileName || "image")}</span>
        <span class="inline-upload-status">准备上传</span>
      </div>
      <div class="progress inline-upload-progress">
        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
      </div>
    `;
    uploadList.appendChild(row);
    return row;
  };

  const setRowProgress = (row, pct, status) => {
    if (!row) return;
    const bar = row.querySelector(".progress-bar");
    const st = row.querySelector(".inline-upload-status");
    if (bar) bar.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    if (st && status) st.textContent = status;
  };

  const markRowDone = (row, ok, status) => {
    if (!row) return;
    const bar = row.querySelector(".progress-bar");
    const st = row.querySelector(".inline-upload-status");
    if (bar) {
      bar.classList.remove("bg-danger", "bg-success");
      bar.classList.add(ok ? "bg-success" : "bg-danger");
      bar.style.width = "100%";
    }
    if (st) st.textContent = status || (ok ? "完成" : "失败");
    
    // 成功上传后3秒自动隐藏
    if (ok) {
      setTimeout(() => {
        if (row && row.parentNode) {
          row.style.transition = "opacity 0.3s, transform 0.3s";
          row.style.opacity = "0";
          row.style.transform = "translateY(-10px)";
          setTimeout(() => {
            if (row && row.parentNode) {
              row.remove();
              // 如果没有其他上传项，隐藏整个容器
              if (uploadList && uploadList.querySelectorAll(".inline-upload-row").length === 0) {
                uploadList.classList.add("d-none");
              }
            }
          }, 300);
        }
      }, 3000);
    }
  };

  const uploadInlineImage = async (file, row) => {
    const payload = new FormData();
    payload.append("image", file, file.name);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", inlineUploadUrl, true);
      xhr.responseType = "json";

      xhr.upload.onprogress = (e) => {
        if (!e.lengthComputable) return;
        const pct = Math.round((e.loaded / e.total) * 100);
        setRowProgress(row, pct, `上传中 ${pct}%`);
      };

      xhr.onload = () => {
        const ok = xhr.status >= 200 && xhr.status < 300;
        const data = xhr.response || {};
        if (!ok || !data || !data.ok) {
          reject(new Error((data && data.error) || `Upload failed (${xhr.status})`));
          return;
        }
        resolve(data);
      };

      xhr.onerror = () => reject(new Error("网络错误"));
      xhr.send(payload);
    });
  };

  const insertUploadedImage = (url, inlineId) => {
    const img = document.createElement("img");
    img.src = url;
    img.alt = "image";
    img.setAttribute("data-inline-id", inlineId);
    img.className = "rte-inline-image";
    insertNodeAtCursor(img);
    insertNodeAtCursor(document.createElement("br"));
    setPlaceholder();
  };

  const insertLocalPlaceholderImage = (file) => {
    const img = document.createElement("img");
    const objectUrl = URL.createObjectURL(file);
    img.src = objectUrl;
    img.alt = "image";
    img.className = "rte-inline-image";
    img.setAttribute("data-inline-pending", "1");
    img.addEventListener(
      "load",
      () => {
        URL.revokeObjectURL(objectUrl);
      },
      { once: true }
    );
    insertNodeAtCursor(img);
    insertNodeAtCursor(document.createElement("br"));
    setPlaceholder();
    syncToHiddenField();
    return img;
  };

  const handleImageFiles = async (files) => {
    const imgs = Array.from(files || []).filter((f) => f && f.type && f.type.startsWith("image/"));
    if (!imgs.length) return;

    editor.focus();

    for (const file of imgs) {
      const row = createUploadRow(file.name);
      const placeholder = insertLocalPlaceholderImage(file);
      pendingUploads += 1;
      try {
        setRowProgress(row, 0, "压缩中");
        const compressed = await compressImage(file);
        setRowProgress(row, 0, "上传中");
        const res = await uploadInlineImage(compressed, row);
        markRowDone(row, true, "完成");
        if (placeholder && placeholder.isConnected) {
          placeholder.src = res.url;
          placeholder.removeAttribute("data-inline-pending");
          placeholder.setAttribute("data-inline-id", res.id);
        } else {
          insertUploadedImage(res.url, res.id);
        }
        syncToHiddenField();
      } catch (e) {
        markRowDone(row, false, "失败");
        if (placeholder && placeholder.isConnected) {
          placeholder.remove();
          syncToHiddenField();
        }
        showToast(e?.message || "图片处理失败", "error");
      } finally {
        pendingUploads = Math.max(0, pendingUploads - 1);
      }
    }
  };

  const handlePaste = async (e) => {
    const dt = e.clipboardData;
    const items = dt?.items ? Array.from(dt.items) : [];
    const images = items.filter((it) => it.kind === "file" && it.type && it.type.startsWith("image/")).map((it) => it.getAsFile()).filter(Boolean);

    if (images.length) {
      e.preventDefault();
      await handleImageFiles(images);
      return;
    }

    const fallbackFiles = dt?.files ? Array.from(dt.files).filter((f) => f.type && f.type.startsWith("image/")) : [];
    if (fallbackFiles.length) {
      e.preventDefault();
      await handleImageFiles(fallbackFiles);
      return;
    }

    if (navigator.clipboard?.read) {
      try {
        const clipboardItems = await navigator.clipboard.read();
        const blobs = [];
        for (const ci of clipboardItems) {
          const types = ci.types || [];
          const imgType = types.find((t) => t.startsWith("image/"));
          if (!imgType) continue;
          const blob = await ci.getType(imgType);
          blobs.push(new File([blob], "pasted-image", { type: imgType }));
        }
        if (blobs.length) {
          e.preventDefault();
          await handleImageFiles(blobs);
        }
      } catch (_) {}
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    editor.classList.remove("is-dragover");
    const files = e.dataTransfer?.files ? Array.from(e.dataTransfer.files) : [];
    if (!files.length) return;
    await handleImageFiles(files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    editor.classList.add("is-dragover");
  };

  const handleDragLeave = () => {
    editor.classList.remove("is-dragover");
  };

  const execToolbarCmd = (cmd) => {
    editor.focus();
    try {
      document.execCommand(cmd, false, null);
    } catch (_) {}
    setPlaceholder();
  };

  document.querySelectorAll(".rte-btn[data-cmd]").forEach((btn) => {
    btn.addEventListener("click", () => execToolbarCmd(btn.dataset.cmd));
  });

  insertImageBtn?.addEventListener("click", () => inlineImagePicker?.click());
  inlineImagePicker?.addEventListener("change", async (e) => {
    const files = e.target?.files;
    if (files && files.length) await handleImageFiles(files);
    e.target.value = "";
  });

  editor.addEventListener("paste", (e) => {
    handlePaste(e);
  });
  editor.addEventListener("drop", (e) => {
    handleDrop(e);
  });
  editor.addEventListener("dragover", (e) => {
    handleDragOver(e);
  });
  editor.addEventListener("dragleave", () => {
    handleDragLeave();
  });
  editor.addEventListener("input", () => {
    setPlaceholder();
    syncToHiddenField();
  });

  const form = document.getElementById("emailForm");
  form?.addEventListener(
    "submit",
    (e) => {
      syncToHiddenField();
      if (pendingUploads > 0) {
        e.preventDefault();
        showToast("图片正在上传中，请稍候再发送", "error");
        return;
      }
    },
    true
  );

  if (contentField.value && contentField.value.trim()) {
    editor.innerHTML = contentField.value;
  }
  setPlaceholder();
  syncToHiddenField();

  window.EmailCompose = {
    sync: syncToHiddenField,
  };
})();
