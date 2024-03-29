from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilterSet
from .permissions import AdminOrReadOnly, AuthorOrAdminOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          FollowUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          RecipeShortSerializer, SetPasswordSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserCreateSerializer, UserReadSerializer)


class UsersViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet,):
    """Вью для users."""

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return UserReadSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserCreateSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'me', 'set_password', 'subscriptions',
                           'subscribe']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        data = request.data
        serializer = self.get_serializer(user, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Пароль успешно изменен'},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Список подписок пользователя."""
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        """Подписка/отписка текущего пользователя на/от автора."""
        author = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            serializer = FollowUserSerializer(author, data=request.data,
                                              context={'request': request,
                                                       'author': author})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        get_object_or_404(Follow, user=request.user,
                          author=author).delete()
        return Response({'detail': 'Успешная отписка'},
                        status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """Вью тэговв."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вью игнидриентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    permission_classes = (AdminOrReadOnly,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вью рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilterSet
    filterset_class = RecipeFilterSet
    serializer_class = RecipeSerializer

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_queryset(self):
        user_id = self.request.user.pk
        return Recipe.objects.add_annotations(user_id).select_related(
            'author').prefetch_related('ingredients', 'tags')


class FavoriteRecipeViewSet(viewsets.ViewSet):
    """Вью для управления избранными рецептами."""

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(AuthorOrAdminOrReadOnly,))
    def favorite(self, request, pk):
        """Добавляет рецепт в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.pk,
            'recipe': recipe.pk
        }
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        message = {
            'detail': 'Рецепт успешно удален из избранного'}
        return Response(message, status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(viewsets.ViewSet):
    """Вью для управления корзиной покупок."""

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=(AuthorOrAdminOrReadOnly,))
    def shopping_cart(self, request, pk):
        """Добавляет рецепт в корзину."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.pk,
            'recipe': recipe.pk
        }
        serializer = ShoppingCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаляет рецепт из корзины."""
        recipe = get_object_or_404(Recipe, pk=pk)
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        message = {
            'detail': 'Рецепт успешно удален из списка покупок'}
        return Response(message, status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartViewSet(viewsets.ViewSet):
    """Вью для загрузки файла с корзиной покупок."""

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Загрузка файла с корзины."""
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')).annotate(
            amount=Sum('amount')
        )
        data = []
        for ingredient in ingredients:
            data.append(
                f'{ingredient["name"]} - '
                f'{ingredient["amount"]} '
                f'{ingredient["measurement_unit"]}'
            )
        content = 'Список покупок:\n\n' + '\n'.join(data)
        filename = 'shopping_cart.txt'
        request = HttpResponse(content, content_type='text/plain')
        request['Content-Disposition'] = f'attachment; filename={filename}'
        return request
