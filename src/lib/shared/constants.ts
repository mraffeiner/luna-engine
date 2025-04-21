export type PageConfig = {
	readonly id: string;
	readonly name: string;
	readonly icon: string;
	readonly serviceId?: string;
};

export type ContentPageConfig = {
	readonly id: string;
	readonly name: string;
	readonly icon: string;
};

export type ServicePageConfig = {
	readonly id: string;
	readonly name: string;
	readonly icon: string;
	readonly serviceId: string;
};

export const PAGES: PageConfig[] = [
	{
		id: 'home',
		name: 'Engine Control Center',
		icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
		serviceId: 'luna-engine'
	},
	{
		id: 'docker-page',
		name: 'Docker Service',
		icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
		serviceId: 'docker-service'
	},
	{
		id: 'prompt-page',
		name: 'Prompt Templates',
		icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z'
	},
	{
		id: 'llm-page',
		name: 'LLM Service',
		icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
		serviceId: 'llm-service'
	},
	{
		id: 'stt-page',
		name: 'STT Service',
		icon: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z',
		serviceId: 'stt-service'
	},
	{
		id: 'tts-page',
		name: 'TTS Service',
		icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z',
		serviceId: 'tts-service'
	},
	{
		id: 'discord-page',
		name: 'Discord Service',
		icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
		serviceId: 'discord-service'
	},
	{
		id: 'chat-page',
		name: 'Chat Service',
		icon: 'M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z', // Chat bubble icon
		serviceId: 'chat-service'
	},
	{
		id: 'alerts-page',
		name: 'Alerts Service',
		icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341A6.002 6.002 0 006 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9', // Bell icon
		serviceId: 'alerts-service'
	},
	{
		id: 'vts-page',
		name: 'VTS Service',
		icon: 'M11.25 5.25v1.5m0 0v1.5m0 0h1.5m-1.5 0h-1.5m3.75 3.75H15v1.5h-1.5v-1.5zm-3.75 0H7.5v1.5h1.5v-1.5zm-3.75 0H3.75v1.5h1.5v-1.5zm11.25 0h-1.5v1.5h1.5v-1.5zM4.5 15.75l-.75.75M19.5 15.75l.75.75M16.5 12a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM6.75 12a.75.75 0 100-1.5.75.75 0 000 1.5zM9 9.75a.75.75 0 11-1.5 0 .75.75 0 011.5 0z', // Game controller icon
		serviceId: 'vts-service'
	},
	{
		id: 'obs-page',
		name: 'OBS Service',
		icon: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z',
		serviceId: 'obs-service'
	}
] as const;

export const SUPPORTED_PLATFORMS = ['twitch', 'youtube'] as const;
export const TTS_ENGINES = ['kokoro', 'azure', 'sesame'] as const;

export const SERVICE_PAGES = PAGES.filter((page) => page.serviceId) as ServicePageConfig[];
export const CONTENT_PAGES = PAGES.filter((page) => !page.serviceId) as ContentPageConfig[];
