// ===== Fade-in on scroll =====
function onScrollFade() {
  const fadeElements = document.querySelectorAll('.fade-in');
  fadeElements.forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight - 50) {
      el.classList.add('visible');
    }
  });
}
window.addEventListener('scroll', onScrollFade);
window.addEventListener('load', onScrollFade);

// ===== Smooth scroll for nav links =====
document.querySelectorAll('nav a').forEach(anchor => {
  anchor.addEventListener('click', e => {
    e.preventDefault();
    const targetID = anchor.getAttribute('href').substring(1);
    const targetSection = document.getElementById(targetID);
    targetSection.scrollIntoView({ behavior: 'smooth' });
  });
});

// ===== Image slideshow / carousel =====
let currentSlide = 0;
const slides = document.querySelectorAll('.slide');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });
}

if (prevBtn && nextBtn) {
  prevBtn.addEventListener('click', () => {
    currentSlide = (currentSlide - 1 + slides.length) % slides.length;
    showSlide(currentSlide);
  });

  nextBtn.addEventListener('click', () => {
    currentSlide = (currentSlide + 1) % slides.length;
    showSlide(currentSlide);
  });

  // Initialize slideshow
  showSlide(currentSlide);
}

// ===== Tabs =====
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(b => b.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// ===== Form validation =====
const contactForm = document.getElementById('contactForm');
const formMsg = document.getElementById('formMsg');

if (contactForm) {
  contactForm.addEventListener('submit', e => {
    e.preventDefault();

    const name = contactForm.name.value.trim();
    const email = contactForm.email.value.trim();
    const message = contactForm.message.value.trim();

    if (!name || !email || !message) {
      formMsg.style.color = '#ff6666';
      formMsg.textContent = 'Please fill in all fields.';
      return;
    }

    if (!validateEmail(email)) {
      formMsg.style.color = '#ff6666';
      formMsg.textContent = 'Please enter a valid email.';
      return;
    }

    formMsg.style.color = 'limegreen';
    formMsg.textContent = 'Thanks for your message! We will get back to you soon.';
    contactForm.reset();
  });
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ===== Dark/Light Mode Toggle =====
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
  });
}

// ===== Animated typing effect =====
const typingText = "Welcome to BababoiOS — Fast, Secure, and Open.";
const typingElem = document.querySelector('.typing');
let index = 0;

const text = "Welcome to BababoiOS — Fast, Secure, and Open.";
let i = 0;

function typeOnce() {
  if (i < text.length) {
    document.querySelector('.typing').textContent += text.charAt(i);
    i++;
    setTimeout(typeOnce, 50);
  }
}

typeOnce();

// ===== Background Music Toggle =====
// Toggle music on/off
const music = document.getElementById('bgMusic');
const musicToggle = document.getElementById('musicToggle');

let isPlaying = true;

musicToggle.addEventListener('click', () => {
  if (isPlaying) {
    music.pause();
    musicToggle.textContent = '🔇';
  } else {
    music.play();
    musicToggle.textContent = '🔊';
  }
  isPlaying = !isPlaying;
});
