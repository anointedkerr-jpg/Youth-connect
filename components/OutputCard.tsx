
import React, { useState } from 'react';
import { PlanningItem } from '../types';
import { Clock, BarChart, BookOpen, ListChecks, Users, Download, Printer, Bookmark, FileText, ChevronDown, ChevronUp, Calendar, Pencil, CalendarPlus, StickyNote, UserCheck } from 'lucide-react';
import { jsPDF } from 'jspdf';
import DatePicker from './DatePicker';

interface OutputCardProps {
  item: PlanningItem;
  isSaved?: boolean;
  onToggleSave?: () => void;
  onUpdate?: (updatedItem: PlanningItem) => void;
  onEdit?: () => void; // Opens the full editor
  compact?: boolean;
  label?: string;
}

const OutputCard: React.FC<OutputCardProps> = ({ item, isSaved = false, onToggleSave, onUpdate, onEdit, compact = false, label }) => {
  const [isExpanded, setIsExpanded] = useState(!compact);

  const toggleExpand = () => setIsExpanded(!isExpanded);

  const handleDateChange = (date: string) => {
    if (onUpdate) {
      onUpdate({ ...item, assignedDate: date });
    }
  };

  const handleDownloadTxt = (e: React.MouseEvent) => {
    e.stopPropagation();
    const content = `
PLAN: ${item.title}
----------------------------------------
Date: ${item.assignedDate || 'Not scheduled'}
Description: ${item.description}
Duration: ${item.suggestedDuration}
Cost: ${item.estimatedCost}
Difficulty: ${item.difficultyLevel}

SCRIPTURE FOCUS:
${item.scriptureReference}

MATERIALS NEEDED:
${item.materialsNeeded.map(m => `- ${m}`).join('\n')}

STEPS:
${item.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}

${item.roles && item.roles.length > 0 ? `TEAM ROLES:\n${item.roles.map(r => `- ${r}`).join('\n')}` : ''}

${item.assignedTeamMembers && item.assignedTeamMembers.length > 0 ? `ASSIGNED MEMBERS:\n${item.assignedTeamMembers.map(m => `- ${m}`).join('\n')}` : ''}

${item.notes ? `NOTES:\n${item.notes}` : ''}
    `.trim();

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${item.title.replace(/\s+/g, '_')}_Plan.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPDF = (e: React.MouseEvent) => {
    e.stopPropagation();
    
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20;
    const maxLineWidth = pageWidth - (margin * 2);
    let yPos = 20;

    // Helper to check for new page
    const checkPageBreak = (heightNeeded: number) => {
      if (yPos + heightNeeded > pageHeight - margin) {
        doc.addPage();
        yPos = 20;
      }
    };

    // Title
    doc.setFontSize(18);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(6, 95, 70); // Emerald 800
    const titleLines = doc.splitTextToSize(item.title, maxLineWidth);
    doc.text(titleLines, margin, yPos);
    yPos += (titleLines.length * 8) + 4;

    // Meta Data
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(100);
    const dateStr = `Date: ${item.assignedDate || 'Not scheduled'}`;
    const metaStr = `${dateStr}  |  Duration: ${item.suggestedDuration}  |  Cost: ${item.estimatedCost}  |  Difficulty: ${item.difficultyLevel}`;
    doc.text(metaStr, margin, yPos);
    yPos += 12;

    // Separator line
    doc.setDrawColor(200);
    doc.line(margin, yPos - 6, pageWidth - margin, yPos - 6);

    // Description
    doc.setFontSize(11);
    doc.setTextColor(0);
    const descLines = doc.splitTextToSize(item.description, maxLineWidth);
    checkPageBreak(descLines.length * 6);
    doc.text(descLines, margin, yPos);
    yPos += (descLines.length * 6) + 10;

    // Scripture
    if (item.scriptureReference && item.scriptureReference !== "N/A") {
      checkPageBreak(20);
      doc.setFont("helvetica", "italic");
      doc.setTextColor(6, 95, 70);
      doc.setFillColor(236, 253, 245); // Emerald 50
      doc.rect(margin, yPos - 4, maxLineWidth, 14, 'F');
      doc.text(`Scripture Focus: ${item.scriptureReference}`, margin + 2, yPos + 4);
      yPos += 18;
    }

    // Steps
    checkPageBreak(20);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.setTextColor(0);
    doc.text("Action Steps:", margin, yPos);
    yPos += 8;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    item.steps.forEach((step, index) => {
      const stepText = `${index + 1}. ${step}`;
      const stepLines = doc.splitTextToSize(stepText, maxLineWidth);
      checkPageBreak(stepLines.length * 6 + 4);
      doc.text(stepLines, margin, yPos);
      yPos += (stepLines.length * 6) + 4;
    });
    yPos += 5;

    // Materials
    if (item.materialsNeeded.length > 0) {
      checkPageBreak(20);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text("Materials Needed:", margin, yPos);
      yPos += 8;
      
      doc.setFont("helvetica", "normal");
      doc.setFontSize(11);
      const materialsText = item.materialsNeeded.join(', ');
      const matLines = doc.splitTextToSize(materialsText, maxLineWidth);
      checkPageBreak(matLines.length * 6);
      doc.text(matLines, margin, yPos);
      yPos += (matLines.length * 6) + 10;
    }

    // Roles
    if (item.roles && item.roles.length > 0) {
      checkPageBreak(20);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text("Team Roles:", margin, yPos);
      yPos += 8;
      
      doc.setFont("helvetica", "normal");
      doc.setFontSize(11);
      item.roles.forEach((role) => {
        checkPageBreak(8);
        doc.text(`• ${role}`, margin, yPos);
        yPos += 7;
      });
    }

    // Assigned Team Members
    if (item.assignedTeamMembers && item.assignedTeamMembers.length > 0) {
      checkPageBreak(20);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text("Assigned Members:", margin, yPos);
      yPos += 8;
      
      doc.setFont("helvetica", "normal");
      doc.setFontSize(11);
      item.assignedTeamMembers.forEach((member) => {
        checkPageBreak(8);
        doc.text(`• ${member}`, margin, yPos);
        yPos += 7;
      });
    }

    // Notes
    if (item.notes) {
      checkPageBreak(20);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text("Notes:", margin, yPos);
      yPos += 8;
      
      doc.setFont("helvetica", "normal");
      doc.setFontSize(11);
      const notesLines = doc.splitTextToSize(item.notes, maxLineWidth);
      checkPageBreak(notesLines.length * 6);
      doc.text(notesLines, margin, yPos);
    }

    // Footer
    doc.setFontSize(9);
    doc.setTextColor(150);
    doc.text("Generated by YouthConnect Ministry Planner", margin, pageHeight - 10);

    doc.save(`${item.title.replace(/\s+/g, '_')}.pdf`);
  };

  const handlePrint = (e: React.MouseEvent) => {
    e.stopPropagation();
    const printWindow = window.open('', '_blank', 'width=800,height=900');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>${item.title} - Print View</title>
            <style>
              body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; color: #1f2937; line-height: 1.5; }
              h1 { color: #059669; border-bottom: 2px solid #059669; padding-bottom: 10px; }
              .meta { display: flex; gap: 20px; font-size: 0.9em; color: #4b5563; margin-bottom: 20px; background: #ecfdf5; padding: 10px; border-radius: 8px; }
              .section-title { font-weight: bold; font-size: 1.1em; margin-top: 25px; margin-bottom: 10px; color: #065f46; display: flex; align-items: center; gap: 8px; }
              ul, ol { margin-top: 5px; padding-left: 20px; }
              li { margin-bottom: 6px; }
              .scripture { background: #f3f4f6; padding: 15px; border-left: 4px solid #059669; font-style: italic; margin: 20px 0; }
              .notes { background: #fffbeb; padding: 15px; border: 1px solid #fcd34d; border-radius: 8px; margin-top: 20px; }
              @media print {
                body { padding: 0; }
                button { display: none; }
              }
            </style>
          </head>
          <body>
            <h1>${item.title}</h1>
            <div class="meta">
              <span><strong>Date:</strong> ${item.assignedDate || 'Not scheduled'}</span>
              <span><strong>Duration:</strong> ${item.suggestedDuration}</span>
              <span><strong>Cost:</strong> ${item.estimatedCost}</span>
              <span><strong>Difficulty:</strong> ${item.difficultyLevel}</span>
            </div>
            
            <p>${item.description}</p>

            ${item.scriptureReference && item.scriptureReference !== 'N/A' ? `
              <div class="scripture">
                <strong>Scripture:</strong> ${item.scriptureReference}
              </div>
            ` : ''}

            <div class="section-title">Action Steps</div>
            <ol>
              ${item.steps.map(step => `<li>${step}</li>`).join('')}
            </ol>

            <div class="section-title">Materials Needed</div>
            <ul>
              ${item.materialsNeeded.map(mat => `<li>${mat}</li>`).join('')}
            </ul>

            ${item.roles && item.roles.length > 0 ? `
              <div class="section-title">Team Roles</div>
              <ul>
                ${item.roles.map(role => `<li>${role}</li>`).join('')}
              </ul>
            ` : ''}

            ${item.assignedTeamMembers && item.assignedTeamMembers.length > 0 ? `
              <div class="section-title">Assigned Members</div>
              <ul>
                ${item.assignedTeamMembers.map(member => `<li>${member}</li>`).join('')}
              </ul>
            ` : ''}

            ${item.notes ? `
              <div class="notes">
                <strong>Notes:</strong><br/>
                ${item.notes.replace(/\n/g, '<br/>')}
              </div>
            ` : ''}
            
            <script>
              window.onload = function() { window.print(); }
            </script>
          </body>
        </html>
      `);
      printWindow.document.close();
    }
  };

  const handleAddToCalendar = (e: React.MouseEvent) => {
    e.stopPropagation();
    // This acts as a trigger to ensure the item is saved and ideally user picks a date
    if (onToggleSave && !isSaved) {
      onToggleSave();
    }
    alert("Saved! Select a date using the date picker above or drag it in the Calendar tab.");
  };

  return (
    <div className={`bg-white rounded-xl shadow-lg border border-emerald-100 overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col h-full ${compact && !isExpanded ? 'bg-gray-50' : ''}`}>
      
      {/* Label Badge for Monthly/Quarterly Views */}
      {label && (
        <div className="bg-emerald-800 text-emerald-100 text-xs font-bold px-3 py-1 uppercase tracking-wider text-center">
          {label}
        </div>
      )}

      <div className={`px-6 py-4 cursor-pointer ${isExpanded ? 'bg-emerald-600' : 'bg-white hover:bg-gray-50'}`} onClick={compact ? toggleExpand : undefined}>
        <div className="flex justify-between items-start gap-4">
          <h3 className={`text-xl font-bold leading-tight ${isExpanded ? 'text-white' : 'text-emerald-900'}`}>{item.title}</h3>
          <div className="flex gap-2 shrink-0">
             <button
               onClick={(e) => { e.stopPropagation(); onEdit ? onEdit() : null; }}
               className={`p-2 rounded-full transition-colors ${
                  isExpanded 
                    ? 'text-emerald-100 hover:bg-emerald-500 hover:text-white' 
                    : 'text-gray-400 hover:text-emerald-600 hover:bg-emerald-50'
                }`}
               title="Edit Idea"
               aria-label="Edit Idea"
               // Only show if onEdit is passed, but style remains for consistency
               style={{ visibility: onEdit ? 'visible' : 'hidden' }}
             >
               <Pencil size={20} />
             </button>

             {onToggleSave && (
              <button 
                onClick={(e) => { e.stopPropagation(); onToggleSave(); }}
                className={`p-2 rounded-full transition-colors ${
                  isExpanded 
                    ? (isSaved ? 'bg-yellow-400 text-emerald-900' : 'bg-emerald-700 text-emerald-100 hover:bg-emerald-500') 
                    : (isSaved ? 'text-yellow-600 bg-yellow-50' : 'text-gray-400 hover:text-emerald-600')
                }`}
                title={isSaved ? "Remove from Saved" : "Save Plan"}
              >
                <Bookmark size={20} fill={isSaved ? "currentColor" : "none"} />
              </button>
            )}

            {compact && (
              <button className={`p-2 rounded-full ${isExpanded ? 'text-white' : 'text-gray-400'}`}>
                {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>
            )}
          </div>
        </div>
        
        {/* Meta tags always visible but styled differently based on state */}
        <div className={`flex flex-wrap gap-3 mt-3 text-sm ${isExpanded ? 'text-emerald-100' : 'text-gray-600'}`}>
           <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${isExpanded ? 'bg-emerald-700 hover:bg-emerald-800' : 'bg-gray-100 hover:bg-gray-200'} transition-colors`} onClick={(e) => e.stopPropagation()}>
            <DatePicker 
              value={item.assignedDate} 
              onChange={handleDateChange} 
              isDark={isExpanded}
            />
          </div>
          <span className={`flex items-center gap-1 px-2 py-1 rounded-full ${isExpanded ? 'bg-emerald-700' : 'bg-gray-100'}`}>
            <Clock size={14} /> {item.suggestedDuration}
          </span>
          <span className={`flex items-center gap-1 px-2 py-1 rounded-full ${isExpanded ? 'bg-emerald-700' : 'bg-gray-100'}`}>
            <BarChart size={14} /> {item.difficultyLevel}
          </span>
        </div>
      </div>

      {isExpanded && (
        <>
          <div className="p-6 space-y-4 flex-grow animate-in fade-in slide-in-from-top-2 duration-200">
            <p className="text-gray-700 italic">{item.description}</p>

            {item.scriptureReference && item.scriptureReference !== "N/A" && (
              <div className="flex items-start gap-2 text-emerald-800 bg-emerald-50 p-3 rounded-lg">
                <BookOpen size={18} className="mt-1 shrink-0" />
                <div>
                  <span className="font-semibold">Scripture Focus:</span> {item.scriptureReference}
                </div>
              </div>
            )}

            {item.roles && item.roles.length > 0 && (
              <div className="border-t pt-4 border-gray-100">
                <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                  <Users size={18} className="text-emerald-600" /> Team Roles
                </h4>
                <ul className="list-disc list-inside text-sm text-gray-600 ml-2">
                  {item.roles.map((role, idx) => (
                    <li key={idx}>{role}</li>
                  ))}
                </ul>
              </div>
            )}

            {item.assignedTeamMembers && item.assignedTeamMembers.length > 0 && (
               <div className="border-t pt-4 border-gray-100">
                 <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                   <UserCheck size={18} className="text-blue-600" /> Assigned Members
                 </h4>
                 <div className="flex flex-wrap gap-2">
                   {item.assignedTeamMembers.map((member, idx) => (
                     <span key={idx} className="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-full border border-blue-100 font-medium">
                       {member}
                     </span>
                   ))}
                 </div>
               </div>
            )}

            <div className="border-t pt-4 border-gray-100">
              <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                <ListChecks size={18} className="text-emerald-600" /> Action Steps
              </h4>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600 ml-1">
                {item.steps.map((step, idx) => (
                  <li key={idx} className="pl-1"><span className="ml-1">{step}</span></li>
                ))}
              </ol>
            </div>

            <div className="border-t pt-4 border-gray-100">
              <h4 className="font-semibold text-gray-900 mb-2 text-sm">Materials Needed:</h4>
              <div className="flex flex-wrap gap-2">
                {item.materialsNeeded.map((mat, idx) => (
                  <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded border border-gray-200">
                    {mat}
                  </span>
                ))}
              </div>
            </div>

            {item.notes && (
               <div className="border-t pt-4 border-gray-100">
                 <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                   <StickyNote size={18} className="text-yellow-500" /> Notes
                 </h4>
                 <p className="text-sm text-gray-600 whitespace-pre-wrap bg-yellow-50 p-3 rounded-lg border border-yellow-100">
                   {item.notes}
                 </p>
               </div>
            )}
          </div>

          {/* Action Footer */}
          <div className="bg-gray-50 border-t border-gray-100 px-6 py-3 flex justify-between items-center flex-wrap gap-2">
            <div className="flex gap-2">
                {onEdit && (
                    <button 
                    onClick={(e) => { e.stopPropagation(); onEdit(); }}
                    className="flex items-center gap-1.5 text-sm text-emerald-700 hover:text-emerald-900 font-medium bg-emerald-100 hover:bg-emerald-200 px-3 py-1.5 rounded-lg transition-colors"
                    title="Edit and customize this idea"
                    aria-label="Edit Idea"
                    >
                    <Pencil size={14} /> Edit Idea
                    </button>
                )}
                 <button 
                  onClick={handleAddToCalendar}
                  className="flex items-center gap-1.5 text-sm text-emerald-700 hover:text-emerald-900 font-medium bg-emerald-100 hover:bg-emerald-200 px-3 py-1.5 rounded-lg transition-colors"
                  title="Add to Calendar / Save"
                >
                  <CalendarPlus size={14} /> <span className="hidden sm:inline">Calendar</span>
                </button>
            </div>

            <div className="flex gap-2">
                <button 
                onClick={handleDownloadTxt}
                className="p-1.5 text-gray-500 hover:text-emerald-600 transition-colors rounded hover:bg-gray-100"
                title="Download as Text File"
                >
                <FileText size={18} />
                </button>
                <button 
                onClick={handleDownloadPDF}
                className="p-1.5 text-gray-500 hover:text-emerald-600 transition-colors rounded hover:bg-gray-100"
                title="Download as PDF"
                >
                <Download size={18} />
                </button>
                <button 
                onClick={handlePrint}
                className="p-1.5 text-gray-500 hover:text-emerald-600 transition-colors rounded hover:bg-gray-100"
                title="Print View"
                >
                <Printer size={18} />
                </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default OutputCard;
