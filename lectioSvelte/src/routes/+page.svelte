<script lang="ts">
	export let data;
	const today = data.today;

	// const month = today.toLocaleString('default', { month: 'long' });
	// const formattedDate = `${month} ${today.getDay()}, ${today.getFullYear()}`;
</script>

<!-- Reading Heading -->
<div class="flex flex-row items-center justify-around">
	<div>button</div>
	<div>
		<h1 class="text-3xl font-semibold">Seventh Sunday of Easter</h1>
		<p>{today}</p>
	</div>
	<div>button</div>
</div>