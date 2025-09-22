// Vue.js application for Agentic Society Web (Vue 3)
const { createApp, ref, reactive, computed, onMounted } = Vue;

const app = createApp({
    setup() {
        const databases = ref([]);
        const selectedDatabase = ref('');
        const personas = ref([]);
        const stats = ref(null);
        const currentView = ref('');
        const errorMessage = ref('');
        const personalityChart = ref(null);
        const lang = ref('zh');

        const menuItems = reactive({
            working_db: { open: true, children: ['personality-browse'] },
            data_analysis: { open: true, children: ['personality-analysis', 'mahalanobis', 'clustering'] },
            special_analysis: { open: true, children: ['multi_mahalanobis', 'identifiability'] },
            progressive_curves: { open: true, children: ['raw_comparison', 'antialign_comparison', 'narrative_comparison', 'curve_comparison'] }
        });

        const languageTexts = {
            zh: {
                working_db: '工作数据库',
                data_analysis: '数据分析',
                special_analysis: '专题分析',
                progressive_curves: 'Progressive Personality Curves',
                'personality-browse': '性格浏览',
                personas: '角色列表',
                'personality-stats': '性格统计',
                'personality-analysis': '性格曲线',
                mahalanobis: '马氏距离分析 (单文件)',
                clustering: '聚类分析 (多文件)',
                stability: '稳定性分析',
                identifiability: '聚类方法可识别性分析',
                multi_mahalanobis: '马氏距离收敛性分析',
                curve_comparison: 'wiki文学形象性格曲线',
                raw_comparison: '正常生成画像性格曲线',
                antialign_comparison: '抗对齐性格曲线',
                narrative_comparison: '叙事方式性格曲线'
            },
            en: {
                working_db: 'Working Database',
                data_analysis: 'Data Analysis',
                special_analysis: 'Special Analysis',
                progressive_curves: 'Progressive Personality Curves',
                'personality-browse': 'Personality Browse',
                personas: 'Personas List',
                'personality-stats': 'Personality Statistics',
                'personality-analysis': 'Personality Curve',
                mahalanobis: 'Mahalanobis Dist (Single File)',
                clustering: 'Clustering (Multi-File)',
                stability: 'Stability Analysis',
                identifiability: 'Clustering Method Identifiability Analysis',
                multi_mahalanobis: 'Mahalanobis Convergence Analysis',
                curve_comparison: 'Wiki Literary Character Personality Curve',
                raw_comparison: 'Normal Generated Profile Personality Curve',
                antialign_comparison: 'Anti-align Personality Curve',
                narrative_comparison: 'Narrative Style Personality Curve'
            }
        };

        const currentLangTexts = computed(() => {
            return languageTexts[lang.value];
        });

        // Load available databases from backend
        const loadDatabases = async () => {
            try {
                const response = await fetch('/api/databases');
                databases.value = await response.json();
            } catch (error) {
                showError('加载数据库列表失败: ' + error.message);
            }
        };

        // Handle database selection change
        const onDatabaseChange = async () => {
            if (selectedDatabase.value) {
                await loadStats();
                currentView.value = ''; // Reset view
            }
        };

        // Load personality statistics
        const loadStats = async () => {
            try {
                const response = await fetch(`/api/personality/stats?db=${encodeURIComponent(selectedDatabase.value)}`);
                stats.value = await response.json();
            } catch (error) {
                showError('加载统计信息失败: ' + error.message);
            }
        };

        // Load personas list
        const loadPersonas = async () => {
            try {
                personas.value = []; // Clear previous data
                const response = await fetch(`/api/personas?db=${encodeURIComponent(selectedDatabase.value)}`);
                personas.value = await response.json();
            } catch (error) {
                showError('加载角色列表失败: ' + error.message);
            }
        };

        // Toggle menu expansion
        const toggleMenu = (menuKey) => {
            menuItems[menuKey].open = !menuItems[menuKey].open;
        };

        // Get iframe source URL for the selected view
        const getFrameSrc = (viewType) => {
            if (!viewType) return '';

            const pageMap = {
                'personality-browse': '/pages/personality/browse-vue3.html',
                'personality-stats': '/pages/personality/stats-vue3.html',
                'personas': '/pages/personas/list-vue3.html',
                'personality-analysis': '/pages/analysis/personality-vue3.html',
                'mahalanobis': '/pages/analysis/mahalanobis-vue3.html',
                'clustering': '/pages/analysis/clustering-vue3.html',
                'identifiability': '/pages/analysis/identifiability.html',
                'multi_mahalanobis': '/pages/analysis/multi_mahalanobis.html',
                'curve_comparison': '/pages/analysis/curve_comparison.html',
                'raw_comparison': '/pages/analysis/raw_comparison.html',
                'antialign_comparison': '/pages/analysis/antialign_comparison.html',
                'narrative_comparison': '/pages/analysis/narrative_comparison.html'
            };

            const pageUrl = pageMap[viewType] || '/pages/placeholder.html';
            return pageUrl;
        };

        // Show different views based on menu selection
        const showView = async (viewType) => {
            currentView.value = viewType;
        };

        // Show personality statistics view
        const showPersonalityStats = async () => {
            if (!stats.value) {
                await loadStats();
            }
            nextTick(() => {
                renderPersonalityChart();
                renderStatsTable();
            });
        };

        // Render statistics table
        const renderStatsTable = () => {
            if (!stats.value) return;

            const tableContainer = document.getElementById('statsTable');
            if (!tableContainer) return;

            // Clear previous content
            tableContainer.innerHTML = '';

            const table = document.createElement('table');
            table.className = 'table table-striped table-hover';

            // Create table header
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>性格维度</th>
                    <th>均值</th>
                    <th>方差</th>
                    <th>标准差</th>
                    <th>样本数</th>
                </tr>
            `;

            // Create table body
            const tbody = document.createElement('tbody');
            const traits = [
                { name: '开放性', key: 'openness' },
                { name: '尽责性', key: 'conscientiousness' },
                { name: '外向性', key: 'extraversion' },
                { name: '宜人性', key: 'agreeableness' },
                { name: '神经质', key: 'neuroticism' }
            ];

            traits.forEach(trait => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${trait.name}</td>
                    <td>${stats.value['avg_' + trait.key] ? stats.value['avg_' + trait.key].toFixed(4) : 'N/A'}</td>
                    <td>${stats.value['var_' + trait.key] ? stats.value['var_' + trait.key].toFixed(4) : 'N/A'}</td>
                    <td>${stats.value['std_' + trait.key] ? stats.value['std_' + trait.key].toFixed(4) : 'N/A'}</td>
                    <td>${stats.value.total_personas || 'N/A'}</td>
                `;
                tbody.appendChild(row);
            });

            table.appendChild(thead);
            table.appendChild(tbody);
            tableContainer.appendChild(table);
        };

        // Show personas list view
        const showPersonas = async () => {
            if (personas.value.length === 0) {
                await loadPersonas();
            }
        };

        // Render personality chart
        const renderPersonalityChart = () => {
            if (!stats.value) return;

            const ctx = document.getElementById('personalityChart');
            if (!ctx) return;

            // Destroy previous chart if exists
            if (personalityChart.value) {
                personalityChart.value.destroy();
            }

            personalityChart.value = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['开放性', '尽责性', '外向性', '宜人性', '神经质'],
                    datasets: [{
                        label: '平均性格特质',
                        data: [
                            stats.value.avg_openness,
                            stats.value.avg_conscientiousness,
                            stats.value.avg_extraversion,
                            stats.value.avg_agreeableness,
                            stats.value.avg_neuroticism
                        ],
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                    }]
                },
                options: {
                    scales: {
                        r: {
                            angleLines: {
                                display: true
                            },
                            suggestedMin: 0,
                            suggestedMax: 5
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        };

        // Format file size
        const formatFileSize = (bytes) => {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };

        // Get current database name
        const getCurrentDbName = () => {
            const db = databases.value.find(db => db.path === selectedDatabase.value);
            return db ? db.name : '';
        };

        // Show error modal
        const showError = (message) => {
            errorMessage.value = message;
            $('#errorModal').modal('show');
        };

        // Return reactive data and methods
        return {
            databases,
            selectedDatabase,
            personas,
            stats,
            currentView,
            errorMessage,
            personalityChart,
            lang,
            menuItems,
            languageTexts,
            currentLangTexts,
            loadDatabases,
            onDatabaseChange,
            loadStats,
            loadPersonas,
            toggleMenu,
            getFrameSrc,
            showView,
            showPersonalityStats,
            renderStatsTable,
            showPersonas,
            renderPersonalityChart,
            formatFileSize,
            getCurrentDbName,
            showError
        };
    }
});

// Mount the app
app.mount('#app');