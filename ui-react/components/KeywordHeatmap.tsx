import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { KeywordStat } from '../types';
import { useLanguage } from '../contexts/LanguageContext';

interface KeywordHeatmapProps {
  data: KeywordStat[];
}

const KeywordHeatmap: React.FC<KeywordHeatmapProps> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { t } = useLanguage();
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Use ResizeObserver to handle tab switches and window resizes robustly
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        if (entry.contentRect.width > 0) {
          setDimensions({
            width: entry.contentRect.width,
            height: 500 // Fixed comfortable height
          });
        }
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    if (!svgRef.current || !data || dimensions.width === 0) return;

    // Clear previous
    d3.select(svgRef.current).selectAll("*").remove();

    const { width, height } = dimensions;
    
    // Color scale based on category
    const color = d3.scaleOrdinal()
      .domain(['emotion', 'object', 'action', 'abstract'])
      .range(['#f472b6', '#60a5fa', '#34d399', '#a78bfa']); 

    // Pack layout
    const pack = d3.pack<KeywordStat>()
      .size([width, height])
      .padding(8); // Increased padding for better separation

    // Transform flat data into hierarchy
    const root = d3.hierarchy({ children: data } as any)
      .sum((d: any) => d.value)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    // Compute layout
    const nodes = pack(root).leaves();

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .style("max-width", "100%")
      .style("height", "auto");

    const node = svg.selectAll("g")
      .data(nodes)
      .join("g")
      .attr("transform", d => `translate(${d.x},${d.y})`);

    // Bubbles
    node.append("circle")
      .attr("r", 0) 
      .attr("fill", (d: any) => color(d.data.category) as string)
      .attr("fill-opacity", 0.2) // Start transparent
      .attr("stroke", (d: any) => color(d.data.category) as string)
      .attr("stroke-width", 2)
      .style("cursor", "default")
      .transition().duration(800).ease(d3.easeBackOut)
      .attr("r", d => d.r)
      .attr("fill-opacity", 0.6); // End opacity

    // Hover effect
    node.on("mouseenter", function() {
      d3.select(this).select("circle")
        .transition().duration(200)
        .attr("fill-opacity", 0.9)
        .attr("stroke-width", 3);
    })
    .on("mouseleave", function() {
      d3.select(this).select("circle")
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
      .style("font-size", d => `${Math.max(12, d.r / 2.2)}px`) 
      .text((d: any) => d.r > 20 ? d.data.text : "");

    // Value labels
    textGroup.append("tspan")
      .attr("x", 0)
      .attr("dy", "1.4em")
      .attr("fill", "rgba(255,255,255,0.9)")
      .style("font-size", d => `${Math.max(10, d.r / 4)}px`)
      .style("font-weight", "normal")
      .text((d: any) => d.r > 30 ? d.data.value : "");

    textGroup.transition().delay(400).duration(500).style("opacity", 1);

    // Tooltip behavior via Title
    node.append("title")
      .text((d: any) => `${d.data.text}\nFrequency: ${d.data.value}\nCategory: ${d.data.category}`);

  }, [data, t, dimensions]); 

  return (
    <div ref={containerRef} className="w-full bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
        <h3 className="text-slate-300 font-semibold flex items-center gap-2 text-lg">
          {t.heatmap.title}
        </h3>
        
        <div className="flex flex-wrap gap-4 text-xs text-slate-400 bg-slate-900/50 px-4 py-2 rounded-lg border border-slate-700/50">
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-pink-400 shadow-[0_0_8px_rgba(244,114,182,0.4)]"></span> {t.heatmap.legend.emotion}</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.4)]"></span> {t.heatmap.legend.object}</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]"></span> {t.heatmap.legend.action}</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(167,139,250,0.4)]"></span> {t.heatmap.legend.abstract}</div>
        </div>
      </div>

      <div className="w-full flex justify-center">
        <svg ref={svgRef} className="w-full block"></svg>
      </div>
    </div>
  );
};

export default KeywordHeatmap;