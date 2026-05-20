// ======================================
// GET DJANGO DATA
// ======================================

const questionAnalytics = JSON.parse(

    document.getElementById(

        'question-data'

    ).textContent
);

// ======================================
// ACCORDION STORAGE
// ======================================

const _chartCharts = new Map();

// ======================================
// EXPAND / COLLAPSE
// ======================================

function setExpanded(bodyEl, expanded){

    if(!bodyEl) return;

    bodyEl.style.display = expanded

        ? 'block'

        : 'none';

    bodyEl.setAttribute(

        'aria-hidden',

        expanded ? 'false' : 'true'
    );
}

// ======================================
// CLOSE OTHER ACCORDIONS
// ======================================

function closeAccordionGroup(

    groupType,
    exceptTargetId

){

    const group = document.querySelectorAll(

        `.accordion-group--${groupType} .question-body`
    );

    group.forEach(body => {

        if(body.id !== exceptTargetId){

            setExpanded(body, false);
        }
    });
}

// ======================================
// ACCORDIONS
// ======================================

function initAccordions(){

    // CLOSE ALL INITIALLY

    document.querySelectorAll(

        '.question-body'

    ).forEach(body => {

        setExpanded(body, false);
    });

    // CLICK EVENTS

    document.querySelectorAll(

        '.question-header'

    ).forEach(header => {

        header.addEventListener(

            'click',

            () => {

                const type = header.getAttribute(

                    'data-accordion-toggle'
                );

                const targetId = header.getAttribute(

                    'data-accordion-target'
                );

                if(!type || !targetId) return;

                const body = document.getElementById(

                    targetId
                );

                const isOpen = (

                    body.style.display === 'block'
                );

                if(!isOpen){

                    closeAccordionGroup(

                        type,
                        targetId
                    );

                    setExpanded(body, true);

                    // CHART INIT

                    if(type === 'chart'){

                        initChartForTargetId(
                            targetId
                        );
                    }

                }else{

                    setExpanded(body, false);
                }
            }
        );

        // KEYBOARD SUPPORT

        header.tabIndex = 0;

        header.addEventListener(

            'keydown',

            (e) => {

                if(

                    e.key === 'Enter'

                    ||

                    e.key === ' '
                ){

                    e.preventDefault();

                    header.click();
                }
            }
        );
    });
}

// ======================================
// CHART INITIALIZATION
// ======================================

function initChartForTargetId(targetId){

    // ALREADY INITIALIZED

    if(_chartCharts.has(targetId)){

        const entry = _chartCharts.get(targetId);

        if(entry && entry.chart){

            entry.chart.resize();
        }

        return;
    }

    // EXTRACT INDEX

    const indexStr = targetId.replace(

        'chart-acc-',
        ''
    );

    const index = parseInt(

        indexStr,
        10
    );

    if(Number.isNaN(index)) return;

    const item = questionAnalytics[index - 1];

    if(!item) return;

    const canvas = document.getElementById(

        `chart-${index}`
    );

    if(!canvas) return;

    // COLORS

    const colors = [

        '#2563eb',
        '#10b981',
        '#f59e0b',
        '#ef4444',
        '#8b5cf6',
        '#06b6d4',
        '#ec4899',
        '#14b8a6'
    ];

    // CHART

    const chart = new Chart(canvas,{

        type:item.chart_type,

        data:{

            labels:item.labels,

            datasets:[{

                label:'Responses',

                data:item.values,

                backgroundColor:

                    item.values.map(

                        (_, i) =>

                        colors[i % colors.length]
                    ),

                borderRadius:20,

                borderSkipped:false,

                borderWidth:0,

                hoverBorderWidth:0,

                barThickness:50,

                maxBarThickness:65
            }]
        },

        options:{

            responsive:true,

            maintainAspectRatio:false,

            animation:{

                duration:1800,

                easing:'easeOutQuart'
            },

            layout:{

                padding:{

                    top:30,
                    right:25,
                    bottom:20,
                    left:20
                }
            },

            plugins:{

                legend:{

                    display:

                        item.chart_type === 'pie'
                        ||
                        item.chart_type === 'doughnut',

                    position:'right',

                    labels:{

                        boxWidth:18,

                        boxHeight:18,

                        padding:20,

                        color:'#334155',

                        font:{

                            size:15,
                            weight:'700'
                        }
                    }
                },

                tooltip:{

                    backgroundColor:'#0f172a',

                    titleColor:'#ffffff',

                    bodyColor:'#e2e8f0',

                    padding:16,

                    cornerRadius:16,

                    displayColors:true,

                    titleFont:{

                        size:15,
                        weight:'700'
                    },

                    bodyFont:{

                        size:14
                    }
                }
            },

            scales:

            item.chart_type === 'pie'

            ||

            item.chart_type === 'doughnut'

            ?

            {}

            :

            {

                y:{

    beginAtZero:true,

    suggestedMax:

    Math.max(...item.values) < 10

    ? 10

    : Math.max(...item.values) + 10,

    border:{
        display:false
    },

    ticks:{

        stepSize:

        Math.ceil(

            Math.max(...item.values) / 10
        ) || 1,

        color:'#64748b',

        font:{

            size:13,
            weight:'600'
        },

        padding:12
    },

    grid:{

        color:

        'rgba(148,163,184,0.12)',

        drawBorder:false
    }
},

                x:{

                    border:{
                        display:false
                    },

                    ticks:{

                        color:'#334155',

                        font:{

                            size:14,
                            weight:'700'
                        },

                        padding:14
                    },

                    grid:{
                        display:false
                    }
                }
            }
        }
    });

    // STORE CHART

    _chartCharts.set(

        targetId,

        { chart }
    );

    // RESIZE

    chart.resize();
}

// ======================================
// DOM LOADED
// ======================================

document.addEventListener(

    'DOMContentLoaded',

    () => {

        initAccordions();
    }
);