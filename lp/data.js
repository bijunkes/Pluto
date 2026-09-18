/**
 * data.js — Pluto site content
 * -----------------------------------------------------------------------
 * All editable content lives here: team members, tech stack, architecture
 * nodes, project context and stats. Update this file to change content
 * without touching the markup or the rendering logic in script.js.
 *
 * To add a real photo for a team member, replace `photo: null` with the
 * image path, e.g. `photo: "assets/team/bianca.jpg"`.
 */

const PLUTO_DATA = {
  team: [
    {
        id: "bianca",
        name: "Bianca Junkes Rech",
        role: "AI & Dev ullstack · Líder",
        lead: true,
        description:
            "Liderança da equipe, desenvolvimento do backend e integração das soluções de Inteligência Artificial.",
        linkedin: "https://br.linkedin.com/in/biancajunkesrech",
        github: "https://github.com/bijunkes",
        photo: "assets/bianca.jpg",
    },
    {
        id: "felipe",
        name: "Felipe Heitor Schmidt",
        role: "Dev Frontend",
        lead: false,
        description:
            "Desenvolvimento das interfaces e construção da experiência visual do Pluto.",
        linkedin: "https://www.linkedin.com/in/felipeheitorschmidt",
        github: "https://github.com/felipeS18",
        photo: "assets/felipe.png",
    },
    {
        id: "gabriel",
        name: "Gabriel Pavesi Corrêa",
        role: "Marketing & Social Media",
        lead: false,
        description:
            "Estratégias de marketing, comunicação e criação de conteúdo para as redes sociais do Pluto.",
        linkedin: "https://www.linkedin.com/in/gabriel-pavesi-corrêa-54a842405/",
        github: "https://github.com/pavesiO-o",
        photo: "assets/gabriel.png",
    },
    {
        id: "luan",
        name: "Luan Patrick Rudolf",
        role: "Dev Fullstack",
        lead: false,
        description:
            "Desenvolvimento fullstack e apoio em diferentes demandas ao longo da construção do projeto.",
        linkedin: "https://www.linkedin.com/in/luan-patrick-rudolf",
        github: "https://github.com/Luan-P-Rudolf",
        photo: "assets/luan.jpg",
    },
    {
        id: "victoria",
        name: "Victória Eloah Schreiner dos Santos",
        role: "Analista de Soluções em IA",
        lead: false,
        description:
            "Análise e apoio na construção de soluções baseadas em Inteligência Artificial para o Pluto.",
        linkedin: "https://www.linkedin.com/in/vict%C3%B3ria-schreiner/",
        github: "https://github.com/victoriaschreiner",
        photo: "assets/victoria.jpg",
    },
],

  techCategories: [
    {
      id: "ia",
      title: "Inteligência Artificial",
      icon: "brain-circuit",
      items: ["Gemini", "Groq"],
    },
    {
      id: "backend",
      title: "Backend",
      icon: "server",
      items: ["Python", "FastAPI", "Uvicorn", "Python Telegram Bot"],
    },
    {
      id: "dados",
      title: "Dados",
      icon: "database",
      items: ["PostgreSQL", "Supabase"],
    },
    {
      id: "frontend",
      title: "Frontend",
      icon: "layout-panel-left",
      items: ["HTML", "CSS", "JavaScript"],
    },
    {
      id: "integracoes",
      title: "Integrações",
      icon: "plug-zap",
      items: ["Telegram", "ngrok", "APIs IA"],
    },
  ],

  // Vertical architecture flow. `branch: true` nodes render side-by-side.
  architecture: [
    { id: "usuario", label: "Usuário", icon: "user", tooltip: "Envia uma mensagem em linguagem natural." },
    { id: "telegram", label: "Telegram", icon: "send", tooltip: "Canal de entrada e saída das conversas." },
    { id: "bot", label: "Telegram Bot", icon: "bot", tooltip: "Recebe e roteia as mensagens do usuário." },
    { id: "services", label: "Services", icon: "layers", tooltip: "Camada de regras de negócio da aplicação." },
    { id: "ia-service", label: "IA Service", icon: "sparkles", tooltip: "Interpreta a mensagem e extrai os dados financeiros." },
    {
      id: "modelos",
      branch: true,
      items: [
        { id: "gemini", label: "Gemini", icon: "gem", tooltip: "Modelo de IA responsável pela interpretação." },
        { id: "groq", label: "Groq", icon: "zap", tooltip: "Inferência de alta velocidade para respostas rápidas." },
      ],
    },
    { id: "db", label: "PostgreSQL / Supabase", icon: "database", tooltip: "Armazena os registros financeiros do usuário." },
    { id: "dashboard", label: "Dashboard", icon: "layout-dashboard", tooltip: "Onde o usuário acompanha sua vida financeira." },
  ],

  context: [
    { label: "Curso", value: "Inteligência Artificial" },
    { label: "Executora", value: "Proway" },
    { label: "Município", value: "Blumenau" },
    { label: "Turno", value: "Vespertino" },
    { label: "Instrutor", value: "Jonas Reiter" },
    { label: "Equipe", value: "Pluto" },
    { label: "Líder", value: "Bianca Junkes Rech" },
  ],

  stats: [
    { value: 5, label: "Integrantes" },
    { value: 1, label: "Assistente financeiro" },
    { value: 2, label: "Modelos de IA" },
    { value: 1, label: "Bot no Telegram" },
    { value: 1, label: "Dashboard" },
  ],

  social: {
    instagram: "https://www.instagram.com/plutoassistente/",
  },
};