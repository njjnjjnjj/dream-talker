<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as d3 from 'd3';
import { type KeywordStat } from '../types';
import { useLanguage } from '../composables/useLanguage';

interface KeywordHeatmapProps {
  data: KeywordStat[];
}

const props = defineProps<KeywordHeatmapProps>();
const svgRef = ref<SVGSVGElement | null>(null);
const containerRef = ref<HTMLDivElement | null>(null);
const { t } = useLanguage();
const dimensions = ref({ width: 0, height: 500 }); // Fixed comfortable height

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  if (!containerRef.value) return;

  resizeObserver = new ResizeObserver(entries => {
    for (let entry of entries) {
      if (entry.contentRect.width > 0) {
        dimensions.value = {
          width: entry.contentRect.width,
          height: 500
        };
      }
    }
  });

  resizeObserver.observe(containerRef.value);
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});

watch([() => props.data, dimensions], () => {
  if (!svgRef.value || !props.data || dimensions.value.width === 0) return;

  nextTick(() => {
    // Clear previous
    d3.select(svgRef.value).selectAll("*").remove();

    const { width, height } = dimensions.value;
    
    // Color scale based on category
    const color = d3.scaleOrdinal<string, string>()
      .domain(['emotion', 'object', 'action', 'abstract'])
      .range(['#f472b6', '#60a5fa', '#34d399', '#a78bfa']); 

    // Pack layout
    const pack = d3.pack<KeywordStat>()
      .size([width, height])
      .padding(8); // Increased padding for better separation

    // Transform flat data into hierarchy
    const root = d3.hierarchy({ children: props.data } as any)
      .sum((d: any) => d.value)
      .sort((a: d3.HierarchyNode<KeywordStat>, b: d3.HierarchyNode<KeywordStat>) => (b.value || 0) - (a.value || 0));

    // Compute layout
    const nodes = pack(root).leaves();

    const svg = d3.select(svgRef.value)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .style("max-width", "100%")
      .style("height", "auto");

    const node = svg.selectAll("g")
      .data(nodes)
      .join("g")
      .attr("transform", (d: d3.HierarchyPointNode<KeywordStat>) => `translate(${d.x},${d.y})`);

    // Bubbles
    node.append("circle")
      .attr("r", 0) 
      .attr("fill", (d: any) => color(d.data.category) as string)
      .attr("fill-opacity", 0.2) // Start transparent
      .attr("stroke", (d: any) => color(d.data.category) as string)
      .attr("stroke-width", 2)
      .style("cursor", "default")
      .transition().duration(800).ease(d3.easeBackOut)
      .attr("r", (d: d3.HierarchyPointNode<KeywordStat>) => d.r)
      .attr("fill-opacity", 0.6); // End opacity

    // Hover effect
    node.on("mouseenter", function(event: MouseEvent, d: any) {
      d3.select(this as SVGGElement).select("circle")
        .transition().duration(200)
        .attr("fill-opacity", 0.9)
        .attr("stroke-width", 3);
    })
    .on("mouseleave", function(event: MouseEvent, d: any) {
      d3.select(this as SVGGElement).select("circle")
        .transition().duration(200)
        .attr("fill-opacity", 0.6)
        .attr("stroke-width", 2);
    });

    // Text labels
    const textGroup = node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.3em")
      .style("pointer-events", "none")
      .style("opacity", 0);

    textGroup.append("tspan")
      .attr("x", 0)
      .attr("dy", "-0.2em")
      .attr("fill", "white")
      .style("font-weight", "bold")
      .style("font-family", "system-ui, sans-serif")
      .style("text-shadow", "0 2px 4px rgba(0,0,0,0.5)")
      .style("font-size", (d: d3.HierarchyPointNode<KeywordStat>) => `${Math.max(12, d.r / 2.2)}px`)
      .text((d: d3.HierarchyPointNode<KeywordStat>) => d.r > 20 ? d.data.text : "");

    // Value labels
    textGroup.append("tspan")
      .attr("x", 0)
      .attr("dy", "1.4em")
      .attr("fill", "rgba(255,255,255,0.9)")
      .style("font-size", (d: d3.HierarchyPointNode<KeywordStat>) => `${Math.max(10, d.r / 4)}px`)
      .style("font-weight", "normal")
      .text((d: d3.HierarchyPointNode<KeywordStat>) => d.r > 30 ? d.data.value : "");

    textGroup.transition().delay(400).duration(500).style("opacity", 1);

    // Tooltip behavior via Title
    node.append("title")
      .text((d: d3.HierarchyPointNode<KeywordStat>) => `${d.data?.text}\nFrequency: ${d.data?.value}\nCategory: ${d.data?.category}`);
  });
}, { deep: true, immediate: true }); 

</script>

<template>
  <div ref="containerRef" class="w-full bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
      <h3 class="text-slate-300 font-semibold flex items-center gap-2 text-lg">
        {{ t.heatmap.title }}
      </h3>
      
      <div class="flex flex-wrap gap-4 text-xs text-slate-400 bg-slate-900/50 px-4 py-2 rounded-lg border border-slate-700/50">
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-pink-400 shadow-[0_0_8px_rgba(244,114,182,0.4)]"></span> {{ t.heatmap.legend.emotion }}</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.4)]"></span> {{ t.heatmap.legend.object }}</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]"></span> {{ t.heatmap.legend.action }}</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(167,139,250,0.4)]"></span> {{ t.heatmap.legend.abstract }}</div>
      </div>
    </div>

    <div class="w-full flex justify-center">
      <svg ref="svgRef" class="w-full block"></svg>
    </div>
  </div>
</template>

<style scoped>
/* Add any scoped styles here if necessary */
</style>