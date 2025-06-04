<script lang="ts">
	import '../app.css';
	import Logo from '$lib/images/Logo.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Lora:ital,wght@0,400..700;1,400..700&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="mx-1 flex flex-col">
	<div class="m-4 mx-10 flex h-24 items-center gap-5 border-b-2 border-amber-100 p-5">
		<a href="/">
			<Logo svgClass="w-32" baseColor="amber-500" hoverColor="amber-400" />
		</a>
		<a href="/"> Links </a>
		<a href="/"> More Links </a>
	</div>

	<div class="items-center text-center">
		{@render children()}
	</div>
</div>
