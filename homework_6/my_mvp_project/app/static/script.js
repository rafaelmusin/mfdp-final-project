document.addEventListener('DOMContentLoaded', () => {
    // --- Элементы для получения рекомендаций ---
    const getRecsButton = document.getElementById('get-recs-btn');
    const userIdRecsInput = document.getElementById('user-id-recs');
    const recsResults = document.getElementById('recs-results');

    // --- Элементы для создания пользователя ---
    const createUserButton = document.getElementById('create-user-btn');
    const createUserResult = document.getElementById('create-user-result');

    // --- Элементы для аналитики ---
    const refreshAnalyticsBtn = document.getElementById('refresh-analytics-btn');
    const totalUsersEl = document.getElementById('total-users');
    const totalItemsEl = document.getElementById('total-items');
    const totalEventsEl = document.getElementById('total-events');
    const totalCategoriesEl = document.getElementById('total-categories');
    const popularItemsChart = document.getElementById('popular-items-chart');
    const activeUsersChart = document.getElementById('active-users-chart');
    const recentEventsList = document.getElementById('recent-events-list');

    // --- Элементы для каталога ---
    const catalogSearch = document.getElementById('catalog-search');
    const catalogSearchBtn = document.getElementById('catalog-search-btn');
    const catalogCategory = document.getElementById('catalog-category');
    const catalogClearBtn = document.getElementById('catalog-clear-btn');
    const catalogCount = document.getElementById('catalog-count');
    const catalogItems = document.getElementById('catalog-items');
    const viewGridBtn = document.getElementById('view-grid-btn');
    const viewListBtn = document.getElementById('view-list-btn');
    const prevPageBtn = document.getElementById('prev-page-btn');
    const nextPageBtn = document.getElementById('next-page-btn');
    const paginationInfo = document.getElementById('pagination-info');

    // --- Модальное окно ---
    const itemModal = document.getElementById('item-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalItemTitle = document.getElementById('modal-item-title');
    const modalItemDetails = document.getElementById('modal-item-details');
    const modalViewBtn = document.getElementById('modal-view-btn');
    const modalCartBtn = document.getElementById('modal-cart-btn');

    // Состояние каталога
    let catalogState = {
        query: '',
        categoryId: null,
        currentPage: 1,
        limit: 12,
        total: 0,
        isGridView: true,
        currentUserId: null
    };

    // --- Функция для выполнения запросов к API ---
    async function apiRequest(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json'
        };

        const config = {
            method: method,
            headers: headers,
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(endpoint, config);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Ошибка HTTP! Статус: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Ошибка запроса к API:', error);
            throw error;
        }
    }

    // --- Функция для показа состояния загрузки ---
    function showLoading(element, message = 'Загрузка...') {
        element.innerHTML = `<div class="loading">${message}</div>`;
    }

    // --- Функция для показа ошибки ---
    function showError(element, message) {
        element.innerHTML = `<div class="error">❌ ${message}</div>`;
    }

    // --- Функция для показа успеха ---
    function showSuccess(element, message) {
        element.innerHTML = `<div style="color: #38a169; background: #c6f6d5; padding: 1rem; border-radius: 8px; border-left: 4px solid #38a169;">✅ ${message}</div>`;
    }

    // --- Функция для анимации чисел ---
    function animateNumber(element, targetNumber, duration = 1000) {
        const startNumber = 0;
        const increment = targetNumber / (duration / 16);
        let currentNumber = startNumber;

        const timer = setInterval(() => {
            currentNumber += increment;
            if (currentNumber >= targetNumber) {
                currentNumber = targetNumber;
                clearInterval(timer);
            }
            element.textContent = Math.floor(currentNumber).toLocaleString();
        }, 16);
    }

    // --- Функция для создания графика ---
    function createBarChart(container, data, labelKey, valueKey, maxValue = null) {
        if (!data || data.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #718096; padding: 2rem;">Нет данных для отображения</p>';
            return;
        }

        const max = maxValue || Math.max(...data.map(item => item[valueKey]));
        
        container.innerHTML = data.map((item, index) => {
            const percentage = max > 0 ? (item[valueKey] / max) * 100 : 0;
            return `
                <div class="chart-item" style="animation-delay: ${index * 0.1}s">
                    <div class="chart-label">${labelKey === 'item_id' ? `ID ${item[labelKey]}` : `ID ${item[labelKey]}`}</div>
                    <div class="chart-bar" style="width: ${percentage}%"></div>
                    <div class="chart-value">${item[valueKey]}</div>
                </div>
            `;
        }).join('');
    }

    // --- Функция для отображения событий ---
    function displayEvents(events) {
        if (!events || events.length === 0) {
            recentEventsList.innerHTML = '<p style="text-align: center; color: #718096; padding: 2rem;">Нет событий для отображения</p>';
            return;
        }

        const eventIcons = {
            'view': '👁️',
            'addtocart': '🛒',
            'transaction': '💰',
            'rate': '⭐'
        };

        const eventNames = {
            'view': 'Просмотр',
            'addtocart': 'В корзину',
            'transaction': 'Покупка',
            'rate': 'Оценка'
        };

        recentEventsList.innerHTML = events.map((event, index) => {
            const icon = eventIcons[event.event_type] || '📝';
            const name = eventNames[event.event_type] || event.event_type;
            const date = new Date(event.timestamp).toLocaleString('ru-RU');
            
            return `
                <div class="event-item event-${event.event_type}" style="animation-delay: ${index * 0.05}s">
                    <div class="event-icon">${icon}</div>
                    <div class="event-info">
                        <div class="event-title">${name}</div>
                        <div class="event-details">Пользователь ${event.user_id} → Товар ${event.item_id}</div>
                    </div>
                    <div class="event-time">${date}</div>
                </div>
            `;
        }).join('');
    }

    // === КАТАЛОГ ФУНКЦИИ ===

    // --- Загрузка категорий ---
    async function loadCategories() {
        try {
            const categories = await apiRequest('/catalog/categories');
            
            catalogCategory.innerHTML = '<option value="">Все категории</option>';
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = `${category.name} (${category.item_count})`;
                catalogCategory.appendChild(option);
            });
            
            console.log('Категории загружены:', categories);
        } catch (error) {
            console.error('Ошибка загрузки категорий:', error);
        }
    }

    // --- Поиск товаров ---
    async function searchItems() {
        try {
            showLoading(catalogItems, 'Поиск товаров...');
            
            const offset = (catalogState.currentPage - 1) * catalogState.limit;
            const params = new URLSearchParams({
                limit: catalogState.limit,
                offset: offset
            });
            
            if (catalogState.query) {
                params.append('q', catalogState.query);
            }
            
            if (catalogState.categoryId) {
                params.append('category_id', catalogState.categoryId);
            }
            
            const response = await apiRequest(`/catalog/search?${params}`);
            
            catalogState.total = response.total;
            displayItems(response.items);
            updatePagination();
            updateCatalogCount();
            
            console.log('Товары найдены:', response);
            
        } catch (error) {
            console.error('Ошибка поиска товаров:', error);
            showError(catalogItems, 'Не удалось загрузить товары');
        }
    }

    // --- Отображение товаров ---
    function displayItems(items) {
        if (!items || items.length === 0) {
            catalogItems.innerHTML = '<p style="text-align: center; color: #718096; padding: 3rem;">Товары не найдены</p>';
            return;
        }

        const itemsHtml = items.map((item, index) => createItemCard(item, index)).join('');
        catalogItems.innerHTML = itemsHtml;
        
        // Добавляем обработчики событий для карточек
        document.querySelectorAll('.item-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.item-action-btn')) {
                    const itemId = card.dataset.itemId;
                    showItemDetails(itemId);
                }
            });
        });
        
        // Обработчики для кнопок действий
        document.querySelectorAll('.item-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const itemId = btn.dataset.itemId;
                handleItemAction(action, itemId);
            });
        });
    }

    // --- Создание карточки товара ---
    function createItemCard(item, index) {
        const cardClass = catalogState.isGridView ? 'item-card' : 'item-card item-card-list';
        
        return `
            <div class="${cardClass}" data-item-id="${item.id}" style="animation-delay: ${index * 0.1}s">
                <div class="item-header">
                    <div class="item-id">Товар ${item.id}</div>
                    <div class="item-category">Каталог товаров</div>
                </div>
                
                <div class="item-properties">
                    <h4>Свойства:</h4>
                    <div class="properties-list">
                        <div class="property-tag">ID: ${item.id}</div>
                        <div class="property-tag">Создан: ${new Date(item.created_at).toLocaleDateString('ru-RU')}</div>
                    </div>
                </div>
                
                <div class="item-stats">
                    <div class="item-actions">
                        <button class="item-action-btn" data-action="view" data-item-id="${item.id}" title="Просмотреть">👁️ Просмотр</button>
                        <button class="item-action-btn" data-action="cart" data-item-id="${item.id}" title="Добавить в корзину">🛒 В корзину</button>
                    </div>
                </div>
            </div>
        `;
    }

    // --- Обработка действий с товаром ---
    async function handleItemAction(action, itemId) {
        if (!catalogState.currentUserId) {
            // Создаем временного пользователя
            try {
                const user = await apiRequest('/users/', 'POST', {});
                catalogState.currentUserId = user.id;
                console.log('Создан временный пользователь:', user.id);
            } catch (error) {
                console.error('Ошибка создания пользователя:', error);
                return;
            }
        }

        const eventType = action === 'view' ? 'view' : 'addtocart';
        const eventData = {
            user_id: catalogState.currentUserId,
            item_id: parseInt(itemId),
            event_type: eventType,
            timestamp: Date.now()
        };

        try {
            await apiRequest('/events/', 'POST', eventData);
            console.log(`Событие ${eventType} создано для товара ${itemId}`);
            
            // Показываем уведомление
            const actionName = action === 'view' ? 'просмотрен' : 'добавлен в корзину';
            showSuccess(document.createElement('div'), `Товар ${itemId} ${actionName}`);
            
            // Обновляем аналитику
            setTimeout(loadAnalytics, 500);
            
        } catch (error) {
            console.error('Ошибка создания события:', error);
        }
    }

    // --- Показ деталей товара ---
    async function showItemDetails(itemId) {
        try {
            modalItemTitle.textContent = `Товар ${itemId}`;
            showLoading(modalItemDetails, 'Загрузка деталей товара...');
            
            const details = await apiRequest(`/catalog/items/${itemId}`);
            
            displayItemDetails(details);
            itemModal.classList.add('show');
            
            // Обновляем кнопки модального окна
            modalViewBtn.onclick = () => handleItemAction('view', itemId);
            modalCartBtn.onclick = () => handleItemAction('cart', itemId);
            
        } catch (error) {
            console.error('Ошибка загрузки деталей товара:', error);
            showError(modalItemDetails, 'Не удалось загрузить детали товара');
        }
    }

    // --- Отображение деталей товара ---
    function displayItemDetails(details) {
        const { item, properties, category, event_stats } = details;
        
        let html = `
            <div class="item-detail">
                <h4>Основная информация</h4>
                <p><strong>ID:</strong> ${item.id}</p>
                <p><strong>Категория:</strong> ${category ? category.name : 'Неизвестна'}</p>
            </div>
        `;
        
        if (properties && properties.length > 0) {
            html += `
                <div class="item-detail">
                    <h4>Свойства товара</h4>
                    <div class="properties-grid">
                        ${properties.map(prop => `
                            <div class="property-item">
                                <div class="property-name">${prop.property}</div>
                                <div class="property-value">${prop.value}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        if (event_stats && event_stats.length > 0) {
            html += `
                <div class="item-detail">
                    <h4>Статистика активности</h4>
                    <ul>
                        ${event_stats.map(stat => `
                            <li>${stat.type}: ${stat.count} событий</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
        
        modalItemDetails.innerHTML = html;
    }

    // --- Обновление счетчика товаров ---
    function updateCatalogCount() {
        const start = (catalogState.currentPage - 1) * catalogState.limit + 1;
        const end = Math.min(catalogState.currentPage * catalogState.limit, catalogState.total);
        catalogCount.textContent = `Показано ${start}-${end} из ${catalogState.total} товаров`;
    }

    // --- Обновление пагинации ---
    function updatePagination() {
        const totalPages = Math.ceil(catalogState.total / catalogState.limit);
        
        prevPageBtn.disabled = catalogState.currentPage <= 1;
        nextPageBtn.disabled = catalogState.currentPage >= totalPages;
        
        paginationInfo.textContent = `Страница ${catalogState.currentPage} из ${totalPages}`;
    }

    // --- Переключение вида ---
    function toggleView(isGrid) {
        catalogState.isGridView = isGrid;
        
        viewGridBtn.classList.toggle('active', isGrid);
        viewListBtn.classList.toggle('active', !isGrid);
        
        catalogItems.className = isGrid ? 'catalog-grid' : 'catalog-list';
        
        // Перерисовываем товары в новом виде
        const items = Array.from(catalogItems.children).map(card => ({
            id: card.dataset.itemId,
            created_at: new Date().toISOString()
        }));
        
        if (items.length > 0) {
            displayItems(items);
        }
    }

    // === ОБРАБОТЧИКИ СОБЫТИЙ КАТАЛОГА ===

    // Поиск
    if (catalogSearchBtn) {
        catalogSearchBtn.addEventListener('click', () => {
            catalogState.query = catalogSearch.value.trim();
            catalogState.currentPage = 1;
            searchItems();
        });
    }

    // Поиск по Enter
    if (catalogSearch) {
        catalogSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                catalogSearchBtn.click();
            }
        });
    }

    // Фильтр по категории
    if (catalogCategory) {
        catalogCategory.addEventListener('change', () => {
            catalogState.categoryId = catalogCategory.value || null;
            catalogState.currentPage = 1;
            searchItems();
        });
    }

    // Очистка фильтров
    if (catalogClearBtn) {
        catalogClearBtn.addEventListener('click', () => {
            catalogSearch.value = '';
            catalogCategory.value = '';
            catalogState.query = '';
            catalogState.categoryId = null;
            catalogState.currentPage = 1;
            searchItems();
        });
    }

    // Переключение видов
    if (viewGridBtn) {
        viewGridBtn.addEventListener('click', () => toggleView(true));
    }
    
    if (viewListBtn) {
        viewListBtn.addEventListener('click', () => toggleView(false));
    }

    // Пагинация
    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => {
            if (catalogState.currentPage > 1) {
                catalogState.currentPage--;
                searchItems();
            }
        });
    }

    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(catalogState.total / catalogState.limit);
            if (catalogState.currentPage < totalPages) {
                catalogState.currentPage++;
                searchItems();
            }
        });
    }

    // Модальное окно
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            itemModal.classList.remove('show');
        });
    }

    // Закрытие модального окна по клику вне его
    if (itemModal) {
        itemModal.addEventListener('click', (e) => {
            if (e.target === itemModal) {
                itemModal.classList.remove('show');
            }
        });
    }

    // --- Функция загрузки аналитики ---
    async function loadAnalytics() {
        try {
            refreshAnalyticsBtn.disabled = true;
            refreshAnalyticsBtn.innerHTML = '🔄 Обновление...';

            // Загружаем статистику
            const [stats, popularItems, activeUsers, recentEvents] = await Promise.all([
                apiRequest('/analytics/stats'),
                apiRequest('/analytics/popular-items?limit=8'),
                apiRequest('/analytics/active-users?limit=8'),
                apiRequest('/analytics/recent-events?limit=15')
            ]);

            // Обновляем общую статистику с анимацией
            animateNumber(totalUsersEl, stats.total_users);
            animateNumber(totalItemsEl, stats.total_items);
            animateNumber(totalEventsEl, stats.total_events);
            animateNumber(totalCategoriesEl, stats.total_categories);

            // Обновляем графики
            createBarChart(popularItemsChart, popularItems, 'item_id', 'event_count');
            createBarChart(activeUsersChart, activeUsers, 'user_id', 'event_count');

            // Обновляем события
            displayEvents(recentEvents);

            console.log('Аналитика успешно загружена:', { stats, popularItems, activeUsers });

        } catch (error) {
            console.error('Ошибка загрузки аналитики:', error);
            
            // Показываем ошибки в соответствующих местах
            showError(popularItemsChart, 'Не удалось загрузить популярные товары');
            showError(activeUsersChart, 'Не удалось загрузить активных пользователей');
            showError(recentEventsList, 'Не удалось загрузить события');
            
        } finally {
            refreshAnalyticsBtn.disabled = false;
            refreshAnalyticsBtn.innerHTML = '🔄 Обновить данные';
        }
    }

    // --- Обработчик кнопки обновления аналитики ---
    if (refreshAnalyticsBtn) {
        refreshAnalyticsBtn.addEventListener('click', loadAnalytics);
    }
    
    // --- Логика получения рекомендаций ---
    if (getRecsButton) {
        getRecsButton.addEventListener('click', async () => {
            const userId = userIdRecsInput.value.trim();
            if (!userId) {
                showError(recsResults, 'Пожалуйста, введите ID пользователя.');
                return;
            }
            
            // Деактивируем кнопку и показываем загрузку
            getRecsButton.disabled = true;
            showLoading(recsResults, 'Получаем рекомендации...');

            try {
                const data = await apiRequest(`/recommendations/${userId}`);
                if (data && data.items && data.items.length > 0) {
                    const itemsHtml = data.items.map((item, index) => 
                        `<li style="animation: slideInLeft 0.3s ease-out ${index * 0.1}s both;">
                            <strong>🛍️ ${item.name || 'Товар'}</strong> 
                            <span style="color: #718096;">(ID: ${item.id})</span>
                            <br>
                            <span style="color: #667eea; font-weight: 600;">⭐ Оценка: ${item.score.toFixed(4)}</span>
                        </li>`
                    ).join('');
                    
                    recsResults.innerHTML = `
                        <h3>🎯 Рекомендации для пользователя ${userId}</h3>
                        <ul style="margin: 0; padding: 0;">${itemsHtml}</ul>
                    `;
                } else {
                    recsResults.innerHTML = `
                        <div style="text-align: center; color: #718096; padding: 2rem;">
                            <div style="font-size: 3rem;">🤷‍♂️</div>
                            <p>Для этого пользователя пока нет рекомендаций.</p>
                        </div>
                    `;
                }
            } catch (error) {
                showError(recsResults, error.message);
            } finally {
                // Активируем кнопку обратно
                getRecsButton.disabled = false;
            }
        });

        // Добавляем возможность нажатия Enter
        userIdRecsInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                getRecsButton.click();
            }
        });
    }

    // --- Логика создания пользователя ---
    if (createUserButton) {
        createUserButton.addEventListener('click', async () => {
            createUserButton.disabled = true;
            showLoading(createUserResult, 'Создаём пользователя...');
            
            try {
                const data = await apiRequest('/users/', 'POST', {});
                if (data && data.id) {
                    showSuccess(createUserResult, `Пользователь создан с ID: <strong>${data.id}</strong>`);
                    
                    // Автоматически подставляем ID в поле рекомендаций
                    if (userIdRecsInput) {
                        userIdRecsInput.value = data.id;
                        userIdRecsInput.focus();
                        
                        // Добавляем небольшую анимацию
                        userIdRecsInput.style.background = '#e6fffa';
                        setTimeout(() => {
                            userIdRecsInput.style.background = '';
                        }, 2000);
                    }

                    // Обновляем аналитику после создания пользователя
                    setTimeout(loadAnalytics, 500);
                } else {
                    showError(createUserResult, 'Не удалось получить ID нового пользователя.');
                }
            } catch (error) {
                showError(createUserResult, error.message);
            } finally {
                createUserButton.disabled = false;
            }
        });
    }

    // --- Добавляем CSS анимации динамически ---
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
    `;
    document.head.appendChild(style);

    // --- Инициализация приложения ---
    loadAnalytics();
    loadCategories();
    searchItems(); // Загружаем первую страницу товаров
}); 