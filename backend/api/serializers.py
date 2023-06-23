from django.contrib.auth.password_validation import validate_password
from django.core.validators import MaxValueValidator, MinValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from foodgram.settings import (MAX_AMOUNT_INGREDIENTS, MAX_COOKING_TIME,
                               MIN_AMOUNT_INGREDIENTS, MIN_COOKING_TIME)
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Tag)
from users.models import User


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор регистрации нового пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        """Проверка введенных данных."""
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        forbidden_usernames = ['me', 'Me', 'ME', 'set_password',
                               'subscriptions', 'subscribe']
        if self.initial_data.get('username') in forbidden_usernames:
            raise serializers.ValidationError(
                {'username': f'Вы не можете использовать {username}'
                 'в качестве "username".'}
            )
        if not first_name:
            raise serializers.ValidationError(
                {'first_name': 'Имя - обязательное поле'}
            )
        if not last_name:
            raise serializers.ValidationError(
                {'last_name': 'Фамилия - обязательное поле'}
            )
        return data


class UserReadSerializer(UserSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, author):
        """Проверка - подписан ли пользователь на автора."""
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return request.user.follower.filter(author=author).exists()
        return False


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля юзера."""
    current_password = serializers.CharField(
        error_messages={'required': 'Обязательное поле.'}
    )
    new_password = serializers.CharField(
        error_messages={'required': 'Обязательное поле.'}
    )

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def update(self, instance, validated_data):
        current_password = validated_data.get('current_password')
        new_password = validated_data.get('new_password')
        if not instance.check_password(current_password):
            raise serializers.ValidationError(
                {
                    'current_password': 'Неверный пароль'
                }
            )
        if current_password == new_password:
            raise serializers.ValidationError(
                {
                    'new_password': 'Новый пароль должен отличаться от '
                                    'текущего пароля'
                }
            )
        instance.set_password(new_password)
        instance.save()
        return validated_data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с кол-вом ингредиентов."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(validators=[
        MinValueValidator(MIN_AMOUNT_INGREDIENTS,
                          'Минимальное количество ингредиентов - '
                          f'{MIN_AMOUNT_INGREDIENTS} ед.'),
        MaxValueValidator(MAX_AMOUNT_INGREDIENTS,
                          'Максимальное количество ингредиентов - '
                          f'{MAX_AMOUNT_INGREDIENTS} ед.'),
    ]
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    tags = TagSerializer(read_only=True, many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        many=True,
        source='ingredients_amount'
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


class RecipeShortSerializer(RecipeSerializer):
    """Сериализатор с краткими сведением рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowUserSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def validate(self, data):
        user = self.context['request'].user
        author = self.context['author']
        if user == author:
            raise serializers.ValidationError(
                {'error': 'Ошибка:Нельзя отписываться/подписываться на себя.'}
            )
        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError(
                {'error': 'Ошибка:Вы уже подписаны на этого автора.'},
            )
        return data

    def get_is_subscribed(self, author):
        """Проверка - подписан ли пользователь на автора."""
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.follower.filter(author=author).exists())


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор авторов, на которых подписан пользовательь.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def get_is_subscribed(self, author):
        """Проверка - подписан ли пользователь на автора."""
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.follower.filter(author=author).exists())

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class RecipeCreateSerializer(RecipeSerializer):
    """Сериализатор для работы с рецептом."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    cooking_time = serializers.IntegerField(validators=[
        MinValueValidator(MIN_COOKING_TIME,
                          'Минимальное время приготовления - '
                          f'{MIN_COOKING_TIME} минута'),
        MaxValueValidator(MAX_COOKING_TIME,
                          'Максимальное время приготовления - '
                          f'{MAX_COOKING_TIME} минуты'),
    ]
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    @staticmethod
    def save_ingredients(recipe, ingredients):
        for ingredient in ingredients:
            current_ingredient = ingredient['ingredient']['id']
            current_amount = ingredient.get('amount')
            obj, created = IngredientAmount.objects.get_or_create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=current_amount
            )
        if created:
            obj.save()

    def validate(self, data):
        ingredients_list = []
        ingredients_amount = data.get('ingredients_amount')
        if not ingredients_amount:
            raise serializers.ValidationError(
                'Укажите минимум 1 ингредиент.'
            )
        for ingredient in ingredients_amount:
            ingredients_list.append(ingredient['ingredient']['id'])
        if len(ingredients_list) > len(set(ingredients_list)):
            raise serializers.ValidationError(
                {'error': 'Ингредиенты не должны повторяться.'}
            )
        return data

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients_amount')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        ingredients = validated_data.pop('ingredients_amount')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.add(*tags)
        self.save_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class FavoriteSerializer(RecipeShortSerializer):
    """Сериализатор Избранного."""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в избранном'
            )
        ]


class ShoppingCartSerializer(RecipeShortSerializer):
    """Сериализатор Корзины."""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в корзине'
            )
        ]
