// 文件树组件 - 独立组件文件
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
                                <ul v-else class="list-unstyled" v-html="renderFileTree(filteredItems)"></ul>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <!-- 选择类型切换 - 只在允许目录选择且不强制只显示目录时显示 -->
                            <div class="me-auto" v-if="allowDirectorySelection && !showOnlyDirectories">
                                <div class="btn-group btn-group-sm" role="group">
                                    <input type="radio" class="btn-check" name="selectionType" id="selectFile" :checked="selectionType === 'file'" @change="handleSelectionTypeChange('file')">
                                    <label class="btn btn-outline-primary" for="selectFile">选择文件</label>
                                    <input type="radio" class="btn-check" name="selectionType" id="selectDirectory" :checked="selectionType === 'directory'" @change="handleSelectionTypeChange('directory')">
                                    <label class="btn btn-outline-primary" for="selectDirectory">选择目录</label>
                                </div>
                            </div>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" @click="confirmSelection" :disabled="!selectedFile">
                                确认选择
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    props: {
        modalTitle: {
            type: String,
            default: '选择文件'
        },
        searchPlaceholder: {
            type: String,
            default: '搜索文件...'
        },
        fileExtension: {
            type: String,
            default: ''
        },
        allowDirectorySelection: {
            type: Boolean,
            default: false
        },
        showOnlyDirectories: {
            type: Boolean,
            default: false
        }
    },
    emits: ['selected'],
    setup(props, { emit }) {
        const searchQuery = ref('');
        const loading = ref(false);
        const selectedFile = ref(null);
        const fileItems = ref([]);
        const filteredItems = ref([]);
        // 如果配置了只显示目录，默认选择类型设为目录
        const selectionType = ref(props.showOnlyDirectories ? 'directory' : 'file'); // 选择类型：file 或 directory

        // 渲染文件树的函数
        const renderFileTree = (items) => {
            const renderItem = (item, level = 0) => {
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

                // 使用data属性存储路径，通过事件委托处理点击
                let html = `
                    <li class="file-tree-node" data-path="${item.path}" data-type="${item.type}">
                        <div class="d-flex align-items-center py-1" style="padding-left: ${level * 20}px">
                            <i class="bi me-2 ${getIconClass(item)}" style="cursor: pointer;"></i>
                            <span class="flex-grow-1" style="cursor: pointer;">
                                ${item.name}
                                ${item.type === 'file' ? `<small class="text-muted ms-2">(${formatFileSize(item.size)})</small>` : ''}
                            </span>
                        </div>
                `;

                if (item.expanded && item.children && item.children.length > 0) {
                    html += `
                        <ul class="list-unstyled">
                            ${item.children.map(child => renderItem(child, level + 1)).join('')}
                        </ul>
                    `;
                }

                html += '</li>';
                return html;
            };

            return items.map(item => renderItem(item)).join('');
        };

        const loadFileTree = async () => {
            loading.value = true;
            try {
                const response = await fetch('/api/databases');
                const treeData = await response.json();

                if (Array.isArray(treeData)) {
                    // 如果配置了只显示目录，过滤掉文件
                    if (props.showOnlyDirectories) {
                        const filterDirectories = (items) => {
                            return items.filter(item => {
                                if (item.type === 'directory') {
                                    // 递归过滤子项
                                    if (item.children && item.children.length > 0) {
                                        item.children = filterDirectories(item.children);
                                    }
                                    return true;
                                }
                                return false;
                            });
                        };

                        fileItems.value = filterDirectories(JSON.parse(JSON.stringify(treeData)));
                    } else {
                        fileItems.value = treeData;
                    }
                    filteredItems.value = fileItems.value;
                } else {
                    console.error('后端返回的数据不是有效的树状结构:', treeData);
                    fileItems.value = [];
                    filteredItems.value = [];
                }
            } catch (error) {
                console.error('加载文件树失败:', error);
                fileItems.value = [];
                filteredItems.value = [];
            } finally {
                loading.value = false;
            }
        };

        const filterTree = () => {
            if (!searchQuery.value.trim()) {
                filteredItems.value = fileItems.value;
                return;
            }

            const query = searchQuery.value.toLowerCase();
            const filterItems = (items) => {
                return items.filter(item => {
                    if (item.name.toLowerCase().includes(query)) {
                        return true;
                    }
                    if (item.children && item.children.length > 0) {
                        const filteredChildren = filterItems(item.children);
                        if (filteredChildren.length > 0) {
                            item.children = filteredChildren;
                            return true;
                        }
                    }
                    return false;
                });
            };

            filteredItems.value = filterItems(JSON.parse(JSON.stringify(fileItems.value)));
        };

        const clearSearch = () => {
            searchQuery.value = '';
            filteredItems.value = fileItems.value;
        };

        const onItemSelected = (item) => {
            selectedFile.value = item;

            // 更新选中状态样式
            const treeContainer = document.querySelector('.file-tree');
            if (treeContainer) {
                // 移除之前的选中状态
                const previousSelected = treeContainer.querySelector('.selected');
                if (previousSelected) {
                    previousSelected.classList.remove('selected');
                }

                // 添加新的选中状态
                const currentSelected = treeContainer.querySelector(`[data-path="${item.path}"]`);
                if (currentSelected) {
                    currentSelected.classList.add('selected');
                }
            }
        };

        const confirmSelection = () => {
            if (selectedFile.value) {
                emit('selected', selectedFile.value);
                const modalElement = document.getElementById('fileTreeModal');
                if (modalElement && typeof bootstrap !== 'undefined') {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    }
                }
            }
        };

        const handleSelectionTypeChange = (type) => {
            selectionType.value = type;
            selectedFile.value = null; // 清除之前的选中状态

            // 清除选中样式
            const treeContainer = document.querySelector('.file-tree');
            if (treeContainer) {
                const selected = treeContainer.querySelector('.selected');
                if (selected) {
                    selected.classList.remove('selected');
                }
            }
        };

        const toggleExpand = (path) => {
            const findItem = (items, targetPath) => {
                for (const item of items) {
                    if (item.path === targetPath) {
                        if (item.type === 'directory') {
                            item.expanded = !item.expanded;
                            // 触发重新渲染
                            filteredItems.value = [...filteredItems.value];
                        }
                        return true;
                    }
                    if (item.children && item.children.length > 0) {
                        if (findItem(item.children, targetPath)) {
                            return true;
                        }
                    }
                }
                return false;
            };

            findItem(fileItems.value, path);
        };

        const toggleSelect = (path) => {
            const findItem = (items, targetPath) => {
                for (const item of items) {
                    if (item.path === targetPath) {
                        // 根据选择类型和项目类型决定是否可以选择
                        if ((item.type === 'file' && selectionType.value === 'file') ||
                            (item.type === 'directory' && props.allowDirectorySelection && selectionType.value === 'directory')) {
                            onItemSelected(item);
                        }
                        return true;
                    }
                    if (item.children && item.children.length > 0) {
                        if (findItem(item.children, targetPath)) {
                            return true;
                        }
                    }
                }
                return false;
            };

            findItem(fileItems.value, path);
        };

        // 处理文件树点击事件
        const handleTreeClick = (event) => {
            const target = event.target;
            const node = target.closest('.file-tree-node');

            if (!node) return;

            const path = node.dataset.path;
            const type = node.dataset.type;

            if (target.tagName === 'I') {
                // 点击图标：展开/收起目录
                if (type === 'directory') {
                    toggleExpand(path);
                }
            } else {
                // 点击文本：选择文件/目录
                if (type === 'file' || (type === 'directory' && props.allowDirectorySelection && selectionType.value === 'directory')) {
                    toggleSelect(path);
                }
            }
        };

        const open = () => {
            loadFileTree();
            const modalElement = document.getElementById('fileTreeModal');
            if (modalElement && typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(modalElement);

                // 添加模态框隐藏事件监听器，用于清理
                modalElement.addEventListener('hidden.bs.modal', () => {
                    const treeContainer = modalElement.querySelector('.file-tree');
                    if (treeContainer) {
                        treeContainer.removeEventListener('click', handleTreeClick);
                    }
                });

                modal.show();

                // 添加事件监听器
                nextTick(() => {
                    const treeContainer = modalElement.querySelector('.file-tree');
                    if (treeContainer) {
                        treeContainer.addEventListener('click', handleTreeClick);
                    }
                });
            }
        };

        onMounted(() => {
            loadFileTree();
        });

        return {
            searchQuery,
            loading,
            selectedFile,
            fileItems,
            filteredItems,
            renderFileTree,
            filterTree,
            clearSearch,
            onItemSelected,
            confirmSelection,
            handleSelectionTypeChange,
            toggleExpand,
            toggleSelect,
            open
        };
    }
};

// Make component globally available
if (typeof window !== 'undefined') {
    window.FileTreeComponent = FileTreeComponent;
}