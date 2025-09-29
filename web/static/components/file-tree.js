// File Tree Component for Agentic Society Web (Vue 3)
// 树状目录文件结构通用组件

const { ref, reactive, computed, onMounted } = Vue;

const FileTreeComponent = {
    template: `
        <div class="file-tree-container">
            <!-- Modal for file selection -->
            <div class="modal fade" id="fileTreeModal" tabindex="-1" aria-labelledby="fileTreeModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="fileTreeModalLabel">
                                <i class="bi bi-folder me-2"></i>{{ modalTitle }}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Search box -->
                            <div class="mb-3">
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="bi bi-search"></i>
                                    </span>
                                    <input type="text" class="form-control" v-model="searchQuery"
                                           :placeholder="searchPlaceholder" @input="filterTree">
                                    <button class="btn btn-outline-secondary" type="button" @click="clearSearch">
                                        <i class="bi bi-x"></i>
                                    </button>
                                </div>
                            </div>

                            <!-- File tree -->
                            <div class="file-tree" style="max-height: 400px; overflow-y: auto;">
                                <div v-if="loading" class="text-center py-3">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">加载中...</span>
                                    </div>
                                </div>
                                <div v-else-if="filteredItems.length === 0" class="text-center py-3 text-muted">
                                    <i class="bi bi-folder-x display-4"></i>
                                    <p class="mt-2">没有找到匹配的文件</p>
                                </div>
                                <ul v-else class="list-unstyled">
                                    <file-tree-node
                                        v-for="item in filteredItems"
                                        :key="item.path"
                                        :item="item"
                                        :level="0"
                                        @select="onFileSelect">
                                    </file-tree-node>
                                </ul>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <div class="me-auto">
                                <small class="text-muted">
                                    已选择: <span class="fw-bold">{{ selectedFile ? selectedFile.name : '无' }}</span>
                                </small>
                            </div>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" @click="confirmSelection"
                                    :disabled="!selectedFile">确认选择</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,

    props: {
        modalTitle: {
            type: String,
            default: '选择数据库文件'
        },
        searchPlaceholder: {
            type: String,
            default: '搜索文件...'
        },
        fileExtension: {
            type: String,
            default: '.db'
        }
    },

    emits: ['selected'],

    setup(props, { emit }) {
        const loading = ref(false);
        const databases = ref([]);
        const searchQuery = ref('');
        const selectedFile = ref(null);
        const fileTree = ref([]);

        // 过滤后的项目
        const filteredItems = computed(() => {
            if (!searchQuery.value) {
                return fileTree.value;
            }

            const query = searchQuery.value.toLowerCase();
            const filterItems = (items) => {
                return items.filter(item => {
                    const nameMatch = item.name.toLowerCase().includes(query);
                    const childrenMatch = item.children ? filterItems(item.children).length > 0 : false;

                    if (item.type === 'directory') {
                        item.expanded = nameMatch || childrenMatch;
                    }

                    return nameMatch || childrenMatch;
                });
            };

            return filterItems(JSON.parse(JSON.stringify(fileTree.value)));
        });

        // 打开模态框
        const open = () => {
            loadDatabases();
            const modal = new bootstrap.Modal(document.getElementById('fileTreeModal'));
            modal.show();
        };

        // 加载数据库列表
        const loadDatabases = async () => {
            loading.value = true;
            try {
                const response = await fetch('/api/databases');
                databases.value = await response.json();
                buildFileTree();
            } catch (error) {
                console.error('加载数据库列表失败:', error);
            } finally {
                loading.value = false;
            }
        };

        // 构建文件树结构
        const buildFileTree = () => {
            const tree = {};

            databases.value.forEach(db => {
                const pathParts = db.path.split(/[\\/]/);
                let currentLevel = tree;

                // 构建目录结构
                for (let i = 0; i < pathParts.length - 1; i++) {
                    const part = pathParts[i];
                    if (!currentLevel[part]) {
                        currentLevel[part] = {
                            name: part,
                            path: pathParts.slice(0, i + 1).join('/'),
                            type: 'directory',
                            expanded: false,
                            children: {}
                        };
                    }
                    currentLevel = currentLevel[part].children;
                }

                // 添加文件
                const fileName = pathParts[pathParts.length - 1];
                currentLevel[fileName] = {
                    name: db.name,
                    path: db.path,
                    type: 'file',
                    size: db.size,
                    fullPath: db.full_path,
                    directory: db.directory
                };
            });

            // 转换为数组格式
            fileTree.value = objectToArray(tree);
        };

        // 将对象转换为数组
        const objectToArray = (obj) => {
            return Object.values(obj).map(item => {
                if (item.children) {
                    item.children = objectToArray(item.children);
                }
                return item;
            });
        };

        // 文件选择事件
        const onFileSelect = (file) => {
            // 取消之前的选择
            clearSelection(fileTree.value);

            // 设置新的选择
            file.selected = true;
            selectedFile.value = file;
        };

        // 清除选择
        const clearSelection = (items) => {
            items.forEach(item => {
                item.selected = false;
                if (item.children) {
                    clearSelection(item.children);
                }
            });
        };

        // 过滤树
        const filterTree = () => {
            // 搜索功能已在computed中实现
        };

        // 清除搜索
        const clearSearch = () => {
            searchQuery.value = '';
        };

        // 确认选择
        const confirmSelection = () => {
            if (selectedFile.value) {
                emit('selected', selectedFile.value);
                const modal = bootstrap.Modal.getInstance(document.getElementById('fileTreeModal'));
                modal.hide();
            }
        };

        onMounted(() => {
            // 初始化Bootstrap模态框事件
            const modal = document.getElementById('fileTreeModal');
            modal.addEventListener('hidden.bs.modal', () => {
                selectedFile.value = null;
                searchQuery.value = '';
                clearSelection(fileTree.value);
            });
        });

        return {
            loading,
            databases,
            searchQuery,
            selectedFile,
            fileTree,
            filteredItems,
            open,
            loadDatabases,
            buildFileTree,
            onFileSelect,
            filterTree,
            clearSearch,
            confirmSelection
        };
    }
};

// File Tree Node Component (Vue 3)
const FileTreeNode = {
    template: `
        <li class="file-tree-item">
            <div class="d-flex align-items-center"
                 :style="{ paddingLeft: (level * 20) + 'px' }"
                 :class="{ 'selected': item.selected }"
                 @click="toggleSelect">

                <!-- Expand/collapse icon for directories -->
                <span v-if="item.type === 'directory'" class="me-1" @click.stop="toggleExpand">
                    <i class="bi" :class="item.expanded ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
                </span>

                <!-- File/folder icon -->
                <span class="me-2">
                    <i class="bi" :class="getIconClass(item)"></i>
                </span>

                <!-- Name -->
                <span class="file-name flex-grow-1" :title="item.path">
                    {{ item.name }}
                </span>

                <!-- File size -->
                <span v-if="item.type === 'file'" class="text-muted small ms-2">
                    {{ formatFileSize(item.size) }}
                </span>
            </div>

            <!-- Children -->
            <ul v-if="item.type === 'directory' && item.expanded && item.children"
                class="list-unstyled">
                <file-tree-node
                    v-for="child in item.children"
                    :key="child.path"
                    :item="child"
                    :level="level + 1"
                    @select="$emit('select', $event)">
                </file-tree-node>
            </ul>
        </li>
    `,

    props: {
        item: Object,
        level: Number
    },

    emits: ['select'],

    setup(props, { emit }) {
        const toggleExpand = () => {
            props.item.expanded = !props.item.expanded;
        };

        const toggleSelect = () => {
            emit('select', props.item);
        };

        const getIconClass = (item) => {
            if (item.type === 'directory') {
                return item.expanded ? 'bi-folder2-open' : 'bi-folder';
            } else {
                return 'bi-file-earmark';
            }
        };

        const formatFileSize = (bytes) => {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };

        return {
            toggleExpand,
            toggleSelect,
            getIconClass,
            formatFileSize
        };
    }
};

// 注册组件
FileTreeComponent.components = {
    'file-tree-node': FileTreeNode
};

// 注册全局组件
if (typeof Vue !== 'undefined') {
    Vue.component('file-tree', FileTreeComponent);
}

export default FileTreeComponent;