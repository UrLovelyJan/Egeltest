/**
 * main.js — Evalúa+ CENEVAL EGEL-PLUS ISOFT
 */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Selección de opciones ─────────────────────────────── */
  const opciones   = document.querySelectorAll('.option-item');
  const btnSig     = document.getElementById('btn-siguiente');
  const btnEnviar  = document.getElementById('btn-enviar-outline');

  if (opciones.length) {
    opciones.forEach(item => {
      item.addEventListener('click', () => {
        opciones.forEach(o => o.classList.remove('selected'));
        item.classList.add('selected');
        const radio = item.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
        if (btnSig)    { btnSig.disabled    = false; }
        if (btnEnviar) { btnEnviar.disabled = false; }
      });
    });
  }

  /* ── Validar antes de enviar ───────────────────────────── */
  const form = document.getElementById('form-respuesta');
  if (form) {
    form.addEventListener('submit', e => {
      const sel = form.querySelector('input[name="respuesta"]:checked');
      if (!sel) {
        e.preventDefault();
        flashMsg('Selecciona una opción antes de continuar.');
      }
    });
  }

  /* ── Animaciones staggered ─────────────────────────────── */
  document.querySelectorAll('.fade-up').forEach((el, i) => {
    el.style.animationDelay = (i * 0.06) + 's';
  });

});


/* ── Marcar para revisar ───────────────────────────────────── */
function marcarRevisar() {
  const btn = event.currentTarget;
  const marked = btn.getAttribute('data-marked');
  if (marked) {
    btn.removeAttribute('data-marked');
    btn.style.background = '';
    btn.style.color = '';
  } else {
    btn.setAttribute('data-marked', '1');
    btn.style.background = '#fffbeb';
    btn.style.color = '#b45309';
  }
}


/* ── Mensaje flotante temporal ─────────────────────────────── */
function flashMsg(texto) {
  const old = document.getElementById('flash-msg');
  if (old) old.remove();
  const div = document.createElement('div');
  div.id = 'flash-msg';
  div.textContent = texto;
  Object.assign(div.style, {
    position: 'fixed', top: '76px', left: '50%', transform: 'translateX(-50%)',
    background: '#1a2f50', color: 'white', padding: '9px 18px',
    borderRadius: '8px', fontSize: '0.85rem', fontWeight: '500',
    zIndex: '9999', boxShadow: '0 4px 16px rgba(15,31,61,.2)',
    animation: 'fadeUp .25s ease both'
  });
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3000);
}


/* ── Confirmar reinicio ─────────────────────────────────────── */
function confirmarReinicio() {
  return confirm('¿Cerrar sesión y comenzar un nuevo simulacro? Se perderá el progreso actual.');
}
